import json
from table_splitting.split_table import *
from table_representation.table_representer import TableRepresenter
from table_representation.table2json import TableProcessor
from GPT_models import models
from GPT_models.models import few_shot, zero_shot, fine_tuning
from GPT_models.follow_up_q import *


def input_generation(splitting, table_representation) : 
    '''
    Generates input file
    
    Parameters
    splitting : "split" or "non_split"
    table_representation : "TSV" or "JSON"
    
    returns : inpur for model test
    '''
    
    with open('input_generation_script.json', 'r', encoding='utf-8') as file:
        data = json.load(file)  # JSON 데이터를 파이썬 객체로 변환

    print("[INPUT_GEN] splitting:", splitting, "| table_representation:", table_representation)

    if splitting == "non_split" : 
        if table_representation == "JSON" : 
            input_path = data["input_generator"]["splitting_HTML"]["table_representation"]["JSON"]["input_path"]
            output_path = data["input_generator"]["splitting_HTML"]["table_representation"]["JSON"]["output_path"]
            print("[INPUT_GEN] input_path:", input_path, "| output_path:", output_path)
            
            json_file_list = os.listdir(input_path)
            
            for i in json_file_list:
                a = i.split('.')[0]
                table_processor = TableProcessor(input_path + a + '.json')
                table_processor.convert_to_json(i, output_path)
        
        if table_representation == "TSV" : 
            input_path = data["input_generator"]["splitting_HTML"]["table_representation"]["TSV"]["input_path"]
            output_path = data["input_generator"]["splitting_HTML"]["table_representation"]["TSV"]["output_path"]
            print("[INPUT_GEN] input_path:", input_path, "| output_path:", output_path)
            table_list = os.listdir(input_path)
            
            for table_element in table_list:
                table_path = os.path.join(input_path, table_element)  # ✅ 여기서 table_path 정의
                print("[INPUT_GEN] Processing table:", table_path)
                table = TableRepresenter(table_path) 
                table.run(table_element, output_path)
                
    elif splitting == "split" :  
        input_json_path = data["input_generator"]["splitting_HTML"]["split"][0]["input_JSON_path"]
        input_pickle_path = data["input_generator"]["splitting_HTML"]["split"][0]["input_pickle_path"]
        input_HTML_path = data["input_generator"]["splitting_HTML"]["split"][0]["input_HTML_path"]
        output_HTML_path = data["input_generator"]["splitting_HTML"]["split"][0]["output_HTML_path"]
        
        body_list = TablePaser(input_json_path, input_HTML_path, input_pickle_path)
        body_list.run()
        table_spliter = DivideHtml(input_HTML_path + '/example_tbl01.html', input_pickle_path + '/example_tbl01.pickle', output_HTML_path)
        table_spliter.run()
        
        if table_representation == "JSON" : 
            input_path = data["input_generator"]["splitting_HTML"]["split"][1]["table_representation"]["JSON"]["input_path"]
            output_path = data["input_generator"]["splitting_HTML"]["split"][1]["table_representation"]["JSON"]["output_path"]
            
            json_file_list = os.listdir(input_path)
            
            for i in json_file_list:
                a = i.split('.')[0]
                table_processor = TableProcessor(input_path + a + '.json')
                table_processor.convert_to_json(i, output_path)
        
        if table_representation == "TSV" : 
            input_path = data["input_generator"]["splitting_HTML"]["split"][1]["table_representation"]["TSV"]["input_path"]
            output_path = data["input_generator"]["splitting_HTML"]["split"][1]["table_representation"]["TSV"]["output_path"]
            
            table_list = os.listdir(input_path)
            for table_element in table_list:
                table_path = os.path.join(input_path, table_element)
                print("[INPUT_GEN] Processing table:", table_path)
                table = TableRepresenter(table_path) 
                table.run(table_element, output_path)
    
    
def model_test(model_, fq):
    '''
    Generates the prediction files in json format
    
    Parameters
    model_ : "few_shot" or "zero_shot" or "fine_tuning"
    fq : True or False
    
    returns : data extraction result
    '''
    print("[MODEL_TEST] model_:", model_, "| fq:", fq)
    with open('input_generation_script.json', 'r', encoding='utf-8') as file:
        data = json.load(file)  
    
    input_path = data["model"][model_]["input_path"]
    output_path = data["model"][model_]["output_path"]
    
    if fq == False : 
        if model_ == "few_shot":
            result = few_shot(input_path, output_path )

        elif model_ == "zero_shot":
            result = zero_shot(input_path, output_path)

        elif model_ == "fine_tuning":
            result = fine_tuning(input_path, output_path)

        else:
            print("Unknown model type")
    
    elif fq == True : 
        
        if model_ == "few_shot":
            few_shot(input_path, output_path )
            assistant = FollowQ(output_path, input_path, output_path)  
            assistant.run('json','split')
        elif model_ == "zero_shot":
            zero_shot(input_path, output_path)
            assistant = FollowQ(output_path, input_path, output_path)  
            assistant.run('json','split')

        elif model_ == "fine_tuning":
            fine_tuning(input_path, output_path)
            assistant = FollowQ(output_path, input_path, output_path)  
            assistant.run('json','split')
            
    print("[MODEL_TEST] input_path:", input_path, "| output_path:", output_path)
    
if __name__ == "__main__":
    input_generation("split", "TSV")
    model_test("few_shot", True)
