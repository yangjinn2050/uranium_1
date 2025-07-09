import json
import os
import re
from openai import OpenAI
import time
from ast import literal_eval
from copy import copy

def fine_tuning(input_path, output_path):
    """
    Test fine_tuning model, generates the prediction of table data extraction in json format.
    You can use OPENAI PLAYGROUND for training the model. 

    Parameters:
    input_path : TSV or JSON table representation path
    output_path : The path where the prediction is saved

    Returns:
    json : prediction of table data extraction
    """     

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    file_list = os.listdir(input_path)

    response = []
    for file in file_list:
        file_path = ''.join([output_path, file])
        file_name = os.path.basename(file_path)
        with open( input_path + file, 'r', encoding='utf-8-sig') as file:
            loaded_data_string = json.load(file) 
            
        completion = client.chat.completions.create(
            model="FINE TUNED MODEL",
            temperature=0,
            messages=[
            {"role": "system", "content": "this task is to take a string as input and convert it to json format. I want to extract the ligand properties below. [chemical_formula, specific_area, pzc, water_contact_angle, initial_uranium_concentration, adsorbent_amount, solution_volume, adsorbent_solution_ratio, adsorption_amount, adsorption_time]. If a property is missing in the input, omit that key. The output must be a JSON object with only the present keys."},
            {"role": "user", "content": str(loaded_data_string)}
            ]
        )
        result = completion.choices[0].message['content']
        response.append(result)
        try:
            dict_1 = literal_eval(result)
            json_file_path = os.path.join(output_path, file_name)
            with open(file_path[:-5]+'.json', "w", encoding="utf-8-sig") as json_file:
                json.dump(dict_1, json_file, indent=4)
        except:
            with open(file_path[:-5]+'.txt', "w", encoding="utf-8-sig") as file:
                file.write(result)
              
              

def few_shot(input_path, output_path) :   
    """
    Test few shot model, generates the prediction of table data extraction in json format.
    You need to give several I/O pairs.

    Parameters:
    input_path : TSV or JSON table representation path
    output_path : The path where the prediction is saved

    Returns:
    json : prediction of table data extraction
    """        
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    file_list = os.listdir(input_path)
    for file_name in file_list : 
        with open(input_path + file_name, 'r', encoding='utf-8') as file:
            text = file.read()
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            frequency_penalty=0,
            presence_penalty=0,
            messages=[
            {"role": "system", "content": "I will extract ligand data from the table and create a JSON format. The JSON should follow: LIGAND_TEMPLATE = {'ligand_name': {PROPERTY_TEMPLATE}}. PROPERTY_TEMPLATE = {'chemical_formula': '', 'specific_area': '', 'pzc': '', 'water_contact_angle': '', 'initial_uranium_concentration': '', 'adsorbent_amount': '', 'solution_volume': '', 'adsorbent_solution_ratio': '', 'adsorption_amount': '', 'adsorption_time': ''}. Use only the keys from PROPERTY_TEMPLATE and do not modify their names. The output must contain only JSON."},
            
            # X I/O PAIRS
            {"role": "user", "content":''},
            {"role": "assistant", "content": ''},
            
            {"role": "user", "content": text}
        ]
    )
        print("===== OpenAI 응답 출력 =====")
        print(response)  # 전체 response 객체
        print("===== 응답 content만 출력 =====")
        print(response.choices[0].message.content)
    
        prediction = response.choices[0].message.content.strip()
        prediction = re.sub(r"^```(?:json)?\s*|```$", "", prediction.strip(), flags=re.MULTILINE)

        base_name = os.path.splitext(file_name)[0]
        output_filename = os.path.join(output_path, base_name)
        os.makedirs(output_path, exist_ok=True)
        
        try : 
            json_data = json.loads(prediction)
            with open(output_filename + '.json', 'w', encoding='utf-8-sig') as json_file:
                json.dump(json_data, json_file, ensure_ascii = False, indent = 4)

        except : 
            json_data = prediction
            with open(output_filename + '.txt', "w", encoding="utf-8-sig") as txt_file:
                txt_file.write(json_data)


def prompt(messages) : 
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        frequency_penalty=0,
        presence_penalty=0,
        messages= messages)
    
    return messages, response.choices[0].message.content


def zero_shot(input_path, output_path) : 
    """
    Test zero shot model, generates the prediction of table data extraction in json format.

    Parameters:
    input_path : TSV or JSON table representation path
    output_path : The path where the prediction is saved

    Returns:
    json : prediction of table data extraction
    """    
    
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    file_list = os.listdir(input_path)

    for file in file_list :
        data = {'question': [], 'answer': []}
        
        with open(input_path + file, 'r', encoding='utf-8') as file:
            table_representer = file.read()

        table_name = file.split('.')[0]

        instruction = "I'm going to convert the information in the table representer into JSON format.\n LIGAND_TEMPLATE = {'ligand_name': {PROPERTY_TEMPLATE}}\n PROPERTY_TEMPLATE = {'chemical_formula': '', 'specific_area': '', 'pzc': '', 'water_contact_angle': '', 'initial_uranium_concentration': '', 'adsorbent_amount': '', 'solution_volume': '', 'adsorbent_solution_ratio': '', 'adsorption_amount': '', 'adsorption_time': ''}\n Table representer is in below \n\n "
        result = {"ligands":[]}

        message_ = [{"role": "system", "content": instruction + table_representer}]

        ligand_q = "Show the ligands present in the table representer as a Python list. Answer must be ONLY python list. Not like '''python ''' Be very very very strict. Other sentences or explanation is not allowed.\n"
        question = ligand_q
        message_.append({"role": "user", "content": question})
        _, cata_answer = prompt(message_) 
        ligand_list = eval(cata_answer)
        data['question'].append(copy(message_))
        data['answer'].append(cata_answer)

        message_.append({"role": "assistant", "content": cata_answer}) # 다음 prompt에 이전 답 추가

        for ligand in ligand_list : 

            performance_template_q = "Create a LIGAND_TEMPLATE filling in the properties of {ligand}  from the table representer, strictly adhering to the following 3 rules:\n\n Rule 1: Use only the keys in PROPERTY_TEMPLATE.\n Rule 2: Set all values of the keys in PROPERTY_TEMPLATE to be " ". DO NOT INSERT ANY VALUE. BE VERY STRICT.\n Rule 3: Answer must be ONLY json format. Only display the JSON (like string not ```json). Other sentences or explanation is not allowed.".format(ligand="'''"+ligand+"'''")
            question = performance_template_q
            message_.append({"role": "user", "content": question})
            _, perfo_answer = prompt(message_)
            
            data['question'].append(copy(message_)) 
            data['answer'].append(perfo_answer)
            
            message_.append({"role": "assistant", "content": perfo_answer})
            property_q = 'In PROPERTY_TEMPLATE, maintain all keys, and fill in values that exist in the table representer. If there are more than two "values" for the same performance, fill in each "value" with the property template and make it into a list. If there is unit information, never create or modify additional keys, but reflect the units in the value.'
            question = property_q
            message_.append({"role": "user", "content": question})
            _, property_answer1 = prompt(message_)
            property_title_caption_q = "Modify the previous version of LIGAND_TEMPLATE based solely on the title and caption. Never modify the keys. Fill in values only for keys that appear in the title or caption."
            data['question'].append(copy(message_)) 
            data['answer'].append(property_answer1)
                
            message_.append({"role": "assistant", "content": property_answer1})
            question = property_title_caption_q
            message_.append({"role": "user", "content": question})
            _, property_answer2 = prompt(message_) 
            
            data['question'].append(copy(message_))
            data['answer'].append(property_answer2)

            message_.append({"role": "assistant", "content": property_answer1})
            delete_q ='Remove keys with no values from previous version of LIGAND_TEMPLATE.'
            question = delete_q
            message_.append({"role": "user", "content": question})
            _, delete_answer = prompt(message_)
            
            data['question'].append(copy(message_))
            data['answer'].append(delete_answer)
            
            ligand_template = json.loads(delete_answer)
            result["ligands"].append(ligand_template)
            
            message_ = [{"role": "system", "content": instruction + table_representer}]
            message_.append({"role": "user", "content": ligand_q})
            message_.append({"role": "assistant", "content": cata_answer})
            
        if len(result["ligands"]) == 1 :
            final_result = result["ligands"][0]

        elif len(result["ligands"]) > 1 :
            final_result = result
        try :     
            with open(output_path +  table_name + ".json", "w") as json_file:
                json.dump(final_result, json_file, indent = 4)
        except : 
            with open(output_path +  table_name + ".txt", "w", encoding="utf-8-sig") as txt_file:
                txt_file.write(final_result)
            

            
