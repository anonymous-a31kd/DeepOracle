from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import re
import json
from langchain.output_parsers import PydanticOutputParser


class QueryLLM:

    model = ''
    api_key = ''
    api_base = ''
    llm = None

    def __init__(self, model, api_key, api_base, temperature=0.7):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=temperature,
            openai_api_key=self.api_key,
            openai_api_base=self.api_base
        )
        

    def extract_test_case_mock(self, template, test_cases, cases_format):
        prompt = PromptTemplate(
            input_variables=["test_cases", "case_format"],
            template=template,
        )
        chain = prompt | self.llm
        response_test_case_mock = chain.invoke({
            "test_cases": test_cases,
            "case_format": cases_format
        })
        return response_test_case_mock.content

    def gen_test_file_python(self, template, signature, test_cases, one_shot):
        prompt = PromptTemplate(
            input_variables=["function_signature", "test_cases", "test_file_shot"],
            template=template,
        )
        chain = prompt | self.llm
        response_test_file_python = chain.invoke({
            "function_signature": signature,
            "test_cases": test_cases,
            "test_file_shot": one_shot
        })
        return response_test_file_python.content


    def repair_output(self, template, test_case_input, rules_json_file):
        prompt = PromptTemplate(
            input_variables=["input_data", "rules_json_file"],
            template=template,
        )
        chain = prompt | self.llm
        response_output = chain.invoke({
            "input_data": test_case_input,
            "rules_json_file": rules_json_file
        })
        return response_output.content
    
    def get_scenario_from_test_prefix(self, template, test_prefix, focal_method, context, javadoc):
        prompt = PromptTemplate(
            input_variables=["test_prefix", "focal_method", "javadoc", "context"],
            template=template,
        )
        chain = prompt | self.llm
        response_scenario = chain.invoke({
            "test_prefix": test_prefix,
            "focal_method": focal_method,
            "javadoc": javadoc,
            "context": context
        })
        return response_scenario.content
    
    def gen_oracle_for_test_prefix(self, template, test_prefix, test_scenario, method_signature, context, javadoc):
        prompt = PromptTemplate(
            input_variables=["test_prefix", "test_scenario", "method_signature", "javadoc", "context"],
            template=template,
        )
        chain = prompt | self.llm
        response_scenario = chain.invoke({
            "test_prefix": test_prefix,
            "test_scenario": test_scenario,
            "method_signature": method_signature,
            "javadoc": javadoc,
            "context": context
        })
        return response_scenario.content
    
    
    def gen_oracle_with_context(self, template, test_prefix, focal_method, javadoc, context):
        prompt = PromptTemplate(
            input_variables=["test_prefix", "focal_method", "javadoc", "context"],
            template=template,
        )
        chain = prompt | self.llm
        response_scenario = chain.invoke({
            "test_prefix": test_prefix,
            "focal_method": focal_method,
            "javadoc": javadoc,
            "context": context,
        })
        return response_scenario.content
    
    def vote_oracle(self, template, test_prefix, test_case1, test_case2):
        prompt = PromptTemplate(
            input_variables=["test_prefix", "test_case_1", "test_case2_"],
            template=template,
        )
        chain = prompt | self.llm
        response_scenario = chain.invoke({
            "test_prefix": test_prefix,
            "test_case_1": test_case1,
            "test_case_2": test_case2,
        })
        return response_scenario.content
    
    def is_Exception(self, template, test_prefix, test_scenario, focal_method, javadoc):
        prompt = PromptTemplate(
            input_variables=["test_prefix", "test_scenario", "focal_method", "javadoc"],
            template=template,
        )
        chain = prompt | self.llm
        response_scenario = chain.invoke({
            "test_prefix": test_prefix,
            "test_scenario": test_scenario,
            "focal_method": focal_method,
            "javadoc": javadoc,
        })
        return response_scenario.content



