import json
import os 
from openai import OpenAI
import pandas as pd

OpenAI.api_key = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

class FollowQ:
    def __init__(self, json_path, representation_path, save_path):
        self.json_path = json_path
        self.representation_path = representation_path
        self.save_path = save_path
        
        # Questions related to ligands
        self.questions_for_ligand = {
            "1_list": ["representation", "Question 1. Please tell me the names of ligands in the contents within the <table> tags of input representation into a Python list. Give me the names of ligands ONLY. Only output the Python list(like string).\n\n"],
            "2_list": ["json", "Question 2. Please tell me the names of ligands from the input json provided by me into a Python list. Only output the Python list(like string).\n\n"],
            "3_list": ["None", "Question 3. Based on the answer to Question 1, modify or remove any ligands from the answer to Question 2 and provide the updated list in Python. Give me the names of ligands ONLY. Only output the Python list.(like string)\n\n"]
            }
        
        # Questions related to performance
        self.questions_for_performance = {
            "1_list": ["json", "Question 1. Inform me about what property type does {ligand_name} have in the input json I provided? Only output the Python list.(like string)\n\n"]
        }
        
        # Questions related to properties
        self.questions_for_property = {
            "1_both": ["json", "Question 1. Provide detailed information about all sublayers of the {element} of {ligand_name} in input json. Remove keys from the dictionary that do not have a value. Present it in either Python list or JSON format. If the {element} is not 'loading', strictly provide it in Python list or JSON format.(like string not ```python and not ```json)\n\n"],
            "2_str": ["None", "Question 2. If there is any occurrence of 'NA', 'na', 'unknown', or similar content in your recent response, Respond with yes or no. You must answer strictly with yes or no.\n\n"],
            "3_dict": ["None", "Question 3. In the answer to question 1, remove any parts corresponding to 'NA', 'na', 'unknown', or similar contents. Show the modified JSON. Only display the JSON. (like string not ```json)\n\n"],
            "4_list": ["representation", "Question 4. Based on the input representation, provide values of the {element} of the {ligand_name} as a Python list. If there is a unit, please provide strictly the value including the unit. The elements of a Python list must be composed of value plus unit. Only output the Python list.(like string not ```python)\n\n"],
            "5_list": ["None", "Question 5. Based on the answer to question 3, provide values of the '''value''' key of the sublayers of the {element} as a Python list. Only output the Python list.(like string not ```python)\n\n"],
            "6_list": ["None", "Question 6. Based on only numerical values, provide a list of elements that exist in the answer to Question 5 but are not present in the the answer to Question 4. Note that unit differences can be ignored if the numbers match. Only output the Python list.(like string not ```python)\n\n"],
            "7_dict": ["json", "Question 7. If elements included in the list that is the answer to question 6 are in the answer to question 1, remove the sub-dictionary containing those elements from the json I provided. If the answer to 6 is a list containing elements, be sure to delete it from json. Show the modified JSON after removal. Only display the JSON. (like string not ```json)\n\n"],
            "8_dict": ["json", "Question 8. Please tell me the final modified json of {ligand_name} by reflecting the answer to question 7 in the json I provided. Only output the JSON of {ligand_name}. the ligand_name is {ligand_name}. The first key of the dictionary should be {ligand_name}. Remove keys from the dictionary that do not have a value. (like string not ```json)"]
            }

        # Questions related to electrolyte, reaction_type, substrate
        self.questions_for_representation = {
            "1_str": ["representation_title", "Question 1. Does the title of the input representation mention any ligands? Please answer with either yes or no.\n\n"],
            "2_str": ["representation_table_caption", "Question 2. Does the table caption of the input representation mention any ligands? Please answer with either yes or no.\n\n"],
            "3_str": ["representation_title", "Question 3. Does the title provide information about ligand properties? Please answer with either yes or no\n\n"],
            "4_str": ["representation_table_caption", "Question 4. Does the table caption provide information about ligand properties? Please answer with either yes or no\n\n"],
            "5_str": ["representation_title", "Question 5. Does the title include ligand-related experimental conditions? Please answer with either yes or no\n\n"],
            "6_str": ["representation_table_caption", "Question 6. Does the table caption include ligand-related experimental conditions? Please answer with either yes or no\n\n"]
            }
        
        # system prompt  
        self.system_prompt = {"role": "system", "content": "You need to modify the JSON representing the table presenter.\n\n JSON template : {'ligand_name' : {PROPERTY_TEMPLATE}}\n PROPERTY_TEMPLATE : {'chemical_formula': '', 'specific_area': '', 'pzc': '', 'water_contact_angle': '', 'initial_uranium_concentration': '', 'adsorbent_amount': '', 'solution_volume': '', 'adsorbent_solution_ratio': '', 'adsorption_amount': '', 'adsorption_time': ''}\n In the JSON template, 'ligand_name' should be replaced with the actual names present in the input representation."}
    
    def input_prompt(self, representation, json_obj, want_type): 
        """
        Generates a formatted input string based on the type of content requested.

        Parameters:
        representation (str): The input representation string containing HTML content.
        json (str): The JSON string to be included in the input.
        want_type (str): The type of content required ('both', 'representation', 'json', 'representation_title', 'representation_table_caption').

        Returns:
        str: The formatted input string.
        """ 
        if isinstance(representation, dict):
            representation = json.dumps(representation, ensure_ascii=False)
        if isinstance(json_obj, dict):
            json_obj = json.dumps(json_obj, ensure_ascii=False)
        # Split the representation string at each occurrence of '</table>'
        splitted_strings = representation.split('</table>')
        # Determine the format based on the requested type
        if want_type == 'both':
            format_for_input = "<input representation>\n" + str(representation) + "\n<input json>\n" + str(json_obj) + "\n\n"
        elif want_type == 'representation':
            format_for_input = "<input representation>\n" + str(representation) + "\n\n"
        elif want_type == 'json':
            format_for_input = "<input json>\n" + str(json_obj) + "\n\n"
        elif want_type == 'representation_title':
            title_string = splitted_strings[0] + '</table>'
            format_for_input = "<input representation>\n" + str(title_string) + "\n\n"
        elif want_type == 'representation_table_caption':
            table_caption_string = splitted_strings[1]
            format_for_input = "<input representation>\n" + str(table_caption_string) + "\n\n"      
                  
        return format_for_input
    
    def load_file(self, file_type, file_path, file_name):
        """
        Loads the content of a file based on the specified type and path.

        Parameters:
        file_type (str): The type of the file (json, html, txt, etc.)
        file_path (str): The path to the file
        file_name (str): The name of the file

        Returns:
        output: The content of the file. The type of the content depends on the file_type.
        
        Raises:
        ValueError: If the file type is unsupported.
        """
        if not file_name.endswith(f".{file_type}"):
            file_name = f"{file_name}.{file_type}"
        full_path = os.path.join(file_path, file_name)
        with open(file_path + file_name, 'r', encoding='utf-8-sig') as f:
            # Load JSON files
            if file_type == 'json':
                output = json.load(f)
            # Read text or HTML files
            elif file_type in ['html', 'txt']:
                output = f.read()
            # Raise an error for unsupported file formats
            else:
                raise ValueError("Unsupported file format.")
        
        return output
          
    def formatting_type(self, key, answer):
        """
        Formats the answer based on the specified key type.

        Parameters:
        key (str): The key indicating the type of format required (e.g., '1_list', '2_dict').
        answer (str): The answer to be formatted.

        Returns:
        The formatted answer, which can be a list or a dictionary based on the key type.
        """
        # Determine the desired format type from the key
        want_type = key.split('_')[1]
        
        # Handle formatting if the desired type is a list
        if want_type == "list":
            if answer[0] == '"' and answer[-1] == '"':
                answer = answer.strip('"')  # Remove surrounding quotes if present
            answer = eval(answer)  # Evaluate the string as a Python expression (e.g., convert to list)
        
        # Handle formatting if the desired type is a dictionary
        elif want_type == "dict":
            if "```" in answer:
                answer = answer.replace("```json", "").replace("```", "")  # Remove markdown code block formatting
            answer = json.loads(answer)  # Parse the string as JSON
        
        return answer
    
    def check_type(self, key, answer):
        """
        Checks if the type of the answer matches the expected type based on the key.

        Parameters:
        key (str): The key indicating the expected type (e.g., '1_list', '2_dict').
        answer (any): The answer whose type needs to be checked.

        Returns:
        tuple: A tuple containing the expected type (str) and a boolean indicating whether the types match.
        """
        # Extract the question number and expected type from the key
        question_number = key.split('_')[0]
        want_type = key.split('_')[1]
        
        # Determine the actual type of the answer
        answer_type = type(answer).__name__
        
        # Check if the expected type matches the actual type
        type_bool = want_type == answer_type
        
        return want_type, type_bool
        
    def prompt(self, Q):
        """
        Sends a list of messages to the OpenAI ChatCompletion API and returns the response.

        Parameters:
        Q (list): A list of message dictionaries to be sent to the API.

        Returns:
        tuple: A tuple containing the original list of messages (Q) and the response content.
        """
        while True:
            try:
                # Send a request to the OpenAI ChatCompletion API
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=Q,
                    temperature=0,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                break  # Exit the loop if the request is successful
            except Exception as e:
                # Print the error message and retry
                print("An error occurred:", e)
        
        # Return the original messages and the content of the response
        return Q, response.choices[0].message.content
    
    def run(self, input_type, split_mode):
        """
        Executes the main process for modifying JSON files based on given questions.

        Parameters:
        input_type (str): The type of input files (e.g., 'json', 'txt').
        split_mode (str): The mode for handling splits (e.g., 'split', 'no-split').

        Returns:
        None
        """
        json_name_list = os.listdir(self.json_path)
        error_file_name = []
        transpose_bool = False
        
        for json_name in json_name_list:
            # try:
                txt_name = json_name.split('.')[0]
                # Load input files
                input_json = self.load_file('json', self.json_path, json_name)
                input_representation = self.load_file(input_type, self.representation_path, txt_name)
                
                # Initialize messages with system prompt 
                messages = [self.system_prompt]

                # Ligand check
                ligand_result = {}
                question_list = []
                answer_list = []
                question_token_list = []
                answer_token_list = []
                final_result = []
                final_json = {"ligands": []}

                # Iterate through ligand questions
                for key, value in self.questions_for_ligand.items():
                    if value[0] != "None":
                        messages.append({"role": "user", "content": self.input_prompt(input_representation, input_json, value[0])})
                    messages.append({"role": "user", "content": value[1]})
                    messages, answer = self.prompt(messages)
                    question_token_list.append(messages)
                    answer_token_list.append(answer)
                    
                    try:
                        mod_answer = self.formatting_type(key, answer)
                    except Exception as e:
                        try:
                            messages, answer = self.prompt(messages)
                            question_token_list.append(messages)
                            answer_token_list.append(answer)
                            question_list.append("Throwing the same message once again")
                            answer_list.append("Throwing the same message once again")
                        except Exception as e:
                            error_file_name.append(json_name)
                            print(json_name)
                            break
                        
                    ligand_result[key[0]] = mod_answer
                    question_list.append(value[1])
                    answer_list.append(mod_answer)

                    print('--------------------------')
                    print(self.questions_for_ligand[key])
                    print(mod_answer)
                    print(ligand_result)
                    print('--------------------------')

                    messages.append({"role": "assistant", "content": answer})
                    if key[0] == '2' and ligand_result["1"] == ligand_result["2"]:
                        print("GO TO THE PERFORMANCE STAGE !!")
                        break   
                        
                # Performance check
                performance_result = {}
                mod_ligand_list = answer_list[-1]

                if len(mod_ligand_list) > 1:
                    transpose_bool = True
                
                for i in range(len(mod_ligand_list)):
                    messages = [self.system_prompt]
                    for key, value in self.questions_for_performance.items():
                        if value[0] != "None":
                            messages.append({"role": "user", "content": self.input_prompt(input_representation, input_json, value[0])})
                        question = value[1].format(ligand_name = '"""'+ mod_ligand_list[i] +'"""')
                        messages.append({"role": "user", "content": question})
                        messages, answer = self.prompt(messages) 
                        question_token_list.append(messages)
                        answer_token_list.append(answer)
                        
                        try:
                            mod_answer = self.formatting_type(key, answer)  
                        except:
                            try:
                                messages, answer = self.prompt(messages) 
                                question_token_list.append(messages)
                                answer_token_list.append(answer)
                            except:
                                error_file_name.append(json_name)

                                break       
                            
                        performance_result[f'{mod_ligand_list[i]}_{key[0]}'] = mod_answer
                        question_list.append(question)
                        answer_list.append(mod_answer)
                        
                        messages.append({"role": "assistant", "content": answer})
                        if key[0] == '3' and performance_result[f'{mod_ligand_list[i]}_3'] == []:
                            print("GO TO THE PROPERTY STAGE !!")
                            break
                                
                    if isinstance(answer_list[-1], list):
                        mod_performance_list = performance_result[f'{mod_ligand_list[i]}_1']
                    else:
                        while not isinstance(answer_list[-1], list):
                            messages.pop()
                            messages, answer = self.prompt(messages)
                            question_token_list.append(messages)
                            answer_token_list.append(answer)
                            mod_answer = self.formatting_type("1_list", answer)
                            question_list.append(question)
                            answer_list.append(mod_answer)
                            mod_performance_list = answer
                            
                    # Property check       
                    property_result = {}
                    skip_questions = False
                    print("#####################")
                    print(mod_performance_list)
                    
                    if mod_performance_list == []:
                        mod_answer = {str(mod_ligand_list[i]): {}}
                    else:    
                        for j in range(len(mod_performance_list)):
                            messages = []
                            messages.append(self.system_prompt)
                            print("@@@@@@@@@@@@")
                            print(mod_performance_list[j])
                            # system prompt 넣어주고, input 표현자, json 넣어주는 코드 
                            # messages = []
                            # messages.append(self.system_prompt)
                        
                            skip_questions = False
                            anwer3_no = False
                            for key, value in self.questions_for_property.items():
                                # 질문 2의 답변이 "no"일 때 질문 3번과 4번 skip하기 위한 조건문
                                if key[0] in ['3','7'] and skip_questions:
                                    print("SKIP THE NEXT QUESTIONS")
                                    question_list.append("SKIP THE NEXT QUESTIONS")
                                    answer_list.append("SKIP THE NEXT QUESTIONS")
                                    if key[0] in ['3','7']:
                                        skip_questions = False
                                    continue  # 질문 3번과 4번 건너뛰기
                                    
                                if value[0] != "None":
                                    messages.append({"role": "user", "content": self.input_prompt(input_representation, input_json, value[0])})
                                    
                                question = value[1].format(ligand_name = '"""'+ mod_ligand_list[i] +'"""', element = '"""'+ mod_performance_list[j] +'"""')
                                messages.append({"role": "user", "content": question})
                                messages, answer = self.prompt(messages) 
                                question_token_list.append(messages)
                                answer_token_list.append(answer)
                                try:
                                    mod_answer = self.formatting_type(key, answer)  
                                except:
                                    try:
                                        messages, answer = self.prompt(messages) 
                                        question_token_list.append(messages)
                                        answer_token_list.append(answer)
                                    except:
                                        print(json_name)
                                        error_file_name.append(json_name)
                                        break   
                                    
                                property_result[mod_ligand_list[i] + '_' + mod_performance_list[j] + '_' + key[0]] = answer
                                question_list.append(question)
                                answer_list.append(mod_answer)
                                
                                print('--------------------------')
                                print(question)
                                print(mod_answer)
                                print('--------------------------')

                                messages.append({"role": "assistant", "content": answer})
                                
                                if key[0] == '2' and mod_answer.lower() == "no":
                                    question_list.append("Question 3. Based on the answer to question 2, remove any parts corresponding to 'NA', 'na', 'unknown', or similar content from the answer to question 1. Show the modified JSON. Only display the JSON. (like string not ```json)")
                                    answer_list.append(str(property_result[mod_ligand_list[i] + '_' + mod_performance_list[j] + '_1']))
                                    messages.append({"role": "user", "content": "Question 3. Based on the answer to question 2, remove any parts corresponding to 'NA', 'na', 'unknown', or similar content from the answer to question 1. Show the modified JSON. Only display the JSON. (like string not ```json)"})    
                                    messages.append({"role": "assistant", "content": property_result[mod_ligand_list[i] + '_' + mod_performance_list[j] + '_1']})                       
                                    skip_questions = True
                                    anwer3_no = True  
                                      
                                if key[0] == '6' and mod_answer == []:
                                    if anwer3_no:
                                        question_list.append("Question 7. If the answer to question 6 is an empty list, just provide the answer to question 1 as it is.")
                                        answer_list.append(str(property_result[mod_ligand_list[i] + '_' + mod_performance_list[j] + '_1']))
                                        messages.append({"role": "user", "content": "Question 7. If the answer to question 6 is an empty list, just provide the answer to question 1 as it is."})    
                                        messages.append({"role": "assistant", "content": property_result[mod_ligand_list[i] + '_' + mod_performance_list[j] + '_1']})                       
                                        skip_questions = True    
                                    else:
                                        question_list.append("Question 7. If the answer to question 6 is an empty list, just provide the answer to question 3 as it is.")
                                        answer_list.append(str(property_result[mod_ligand_list[i] + '_' + mod_performance_list[j] + '_3']))
                                        messages.append({"role": "user", "content": "Question 7. If the answer to question 6 is an empty list, just provide the answer to question 3 as it is."})    
                                        messages.append({"role": "assistant", "content": property_result[mod_ligand_list[i] + '_' + mod_performance_list[j] + '_3']})                       
                                        skip_questions = True                                           
                                                
                            if isinstance(mod_answer, dict):
                                input_json = mod_answer
                            else:
                                count = 0
                                while not isinstance(mod_answer, dict) and count < 3:
                                    messages.pop()
                                    messages.append({"role": "user", "content": self.input_prompt(input_representation, input_json, 'json')})
                                    messages, answer = self.prompt(messages)
                                    question_token_list.append(messages)
                                    answer_token_list.append(answer)
                                    try:
                                        mod_answer = self.formatting_type(key, answer)  
                                    except:
                                        try:
                                            messages, answer = self.prompt(messages) 
                                            question_token_list.append(messages)
                                            answer_token_list.append(answer)
                                        except:
                                            print('#$@%@#%@#%#@%@#%@#')
                                            print(json_name)
                                            print('#$@%@#%@#%#@%@#%@#')
                                            error_file_name.append(json_name)
                                            break   
                                        
                                    count += 1  
                                    
                                    property_result[mod_ligand_list[i] + '_' + mod_performance_list[j] + '_' + key[0]] = answer
                                    question_list.append(question)
                                    answer_list.append(mod_answer)
                                    
                                    print('--------------------------')
                                    print(question)
                                    print(mod_answer)
                                    print('--------------------------')
                                     
                                    messages.append({"role": "assistant", "content": answer})
                                                    
                    if len(mod_ligand_list) == 1 and split_mode == 'split':
                        final_result.append(mod_answer)
                    else:
                        input_json = self.load_file(input_type, self.json_path, json_name)
                        final_json["ligands"].append(mod_answer)

                if transpose_bool:
                    final_result.append(final_json)
                    
                # Final JSON after property modifications
                if final_result[0] == []:
                    input_json = self.load_file('json', self.json_path, json_name)     
                    new_json = input_json            
                else:
                    new_json = final_result[0] 
                    
                # Handle representation questions
                remove_elements = []
                representation_result = {}
                for key, value in self.questions_for_representation.items():    
                    messages = []                    
                    if value[0] == "None":
                        pass
                    else:  
                        messages.append({"role": "user", "content": self.input_prompt(input_representation, new_json, value[0])})

                    question = value[1]   
                    messages.append({"role": "user", "content": question})
                    messages, answer = self.prompt(messages) 
                    question_token_list.append(messages)
                    answer_token_list.append(answer)

                    mod_answer = self.formatting_type(key, answer)  

                    question_list.append(question)
                    answer_list.append(mod_answer)
                    
                    print('--------------------------')
                    print(question)
                    print(mod_answer)
                    print('--------------------------')

                    messages.append({"role": "assistant", "content": answer})
                    representation_result[key[0]] = mod_answer.replace(".", "").lower()
                    
                if representation_result['1'] == 'no' and representation_result['2'] == 'no':
                    remove_elements.append('reaction_type')
                if representation_result['3'] == 'no' and representation_result['4'] == 'no':
                    remove_elements.append('substrate')
                if representation_result['5'] == 'no' and representation_result['6'] == 'no':
                    remove_elements.append('electrolyte')
                
                remove_elements = list(set(remove_elements))
                
                if remove_elements != []:    
                    for delete_element in remove_elements:
                        messages = []
                        messages.append({"role": "user", "content": self.input_prompt(input_representation, new_json, 'json')})
                        question = "Remove all elements with the key name {delete_element} from the input JSON and display it in only JSON format. Other explanation is not allowed. Show me only JSON result. Only display the JSON. (like string not ```json)".format(delete_element="'''"+delete_element+"'''")
                        messages.append({"role": "user", "content": question})
                        messages, answer = self.prompt(messages)
                        question_token_list.append(messages)
                        answer_token_list.append(answer)
                        try:
                            mod_answer = self.formatting_type('1_dict', answer) 
                        except:
                            try:
                                messages, answer = self.prompt(messages) 
                                question_token_list.append(messages)
                                answer_token_list.append(answer)
                            except:
                                print('#$@%@#%@#%#@%@#%@#')
                                print(json_name)
                                print('#$@%@#%@#%#@%@#%@#')
                                error_file_name.append(json_name)
                                break  
                            
                        question_list.append(question)
                        answer_list.append(mod_answer)    
                        print('--------------------------')
                        print(question)
                        print('answer')
                        print(answer)
                        print('mod answer')
                        print(mod_answer)
                        print('--------------------------')   
                        
                        if not isinstance(mod_answer, dict):  
                            count = 0
                            while not isinstance(mod_answer, dict) and count < 3:
                                # 원래 했던 질문 제거하고 다시 
                                messages, answer = self.prompt(messages)
                                question_token_list.append(messages)
                                answer_token_list.append(answer)
                                try:
                                    mod_answer = self.formatting_type('1_dict', answer)  
                                except:
                                    try:
                                        messages, answer = self.prompt(messages) 
                                        question_token_list.append(messages)
                                        answer_token_list.append(answer)
                                    except:
                                        print('#$@%@#%@#%#@%@#%@#')
                                        print(json_name)
                                        print('#$@%@#%@#%#@%@#%@#')
                                        error_file_name.append(json_name)
                                        break   
                                    
                                count += 1    
                                question_list.append(question)
                                answer_list.append(mod_answer)  
                                  
                                print('--------------------------')
                                print(question)
                                print(mod_answer)
                                print('--------------------------')
                                
                        if not isinstance(mod_answer, dict): 
                            new_json = new_json
                        else:                                       
                            new_json = mod_answer
                else:
                    mod_answer = new_json

                # Ensure the necessary directories exist
                os.makedirs(os.path.join(self.save_path, 'log'), exist_ok=True)
                os.makedirs(os.path.join(self.save_path, 'token'), exist_ok=True)
                os.makedirs(os.path.join(self.save_path, 'json'), exist_ok=True)
                
                # Save the modified JSON and log
                if json_name not in error_file_name:
                    log_path = self.save_path + 'log/'+ txt_name
                    df = pd.DataFrame({'Question': question_list, 'GPT answer': answer_list})
                    df.to_csv(log_path+'.csv', index=False)
                    
                    token_path = self.save_path + 'token/'+ txt_name
                    token_df = pd.DataFrame({'Question': question_token_list, 'GPT answer': answer_token_list})
                    token_df.to_csv(token_path+'.csv', index=False)
                    
                    new_json_path = self.save_path + 'json/'+ json_name
                    if mod_answer == [] :
                        input_json = self.load_file('json', self.json_path, json_name)
                        with open(new_json_path, "w") as json_file:
                            json.dump(input_json, json_file, indent=4)                        
                    else:
                        if isinstance(mod_answer, list):
                            with open(new_json_path, "w") as json_file:
                                json.dump(new_json, json_file, indent=4)
                                
                        elif isinstance(mod_answer, str):
                            with open(new_json_path, "w") as json_file:
                                json.dump(new_json, json_file, indent=4)
                        else:
                            with open(new_json_path, "w") as json_file:
                                json.dump(mod_answer, json_file, indent=4)

                          
if __name__ == "__main__":
    representation_path = 'table representer path'
    json_path = 'gpt prediction'
    save_path = 'save path'
    
    assistant = FollowQ(json_path, representation_path, save_path)  
    assistant.run('txt', 'split') 
    
        
