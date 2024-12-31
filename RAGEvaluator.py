from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from rouge_score import rouge_scorer
from bert_score import score
import numpy as np
import pandas as pd
import os
from typing import List, Dict, Tuple
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from SqliteClient import SqliteClient


class RAGEvaluator:
    def __init__(self,rag):
        """
        Initialize the RAG evaluator with OpenAI API key and necessary models
        """
        self.rag = rag
        self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
        self.sqlient = SqliteClient ("sb-docs")

    def get_rag_response(self, question: str) -> str:
        """
        Get response from the RAG pipeline using LangChain and OpenAI
        """
        message = HumanMessage(content=question)
        sys_message_content , picked_chunks = self.rag.get_prompt(question)
        system_message = SystemMessage(content=sys_message_content)
        model_messages = [system_message] + [message]
        response = self.rag.chat_model(model_messages)
        return response

    def calculate_rouge_scores(self, prediction: str, reference: str) -> Dict[str, float]:
        """
        Calculate ROUGE-1 and ROUGE-L scores
        """
        scores = self.rouge_scorer.score(prediction, reference)
        return {
            'rouge1': scores['rouge1'].fmeasure,
            'rougeL': scores['rougeL'].fmeasure
        }

    def calculate_bert_score(self, prediction: str, reference: str) -> float:
        """
        Calculate BERTScore
        """
        P, R, F1 = score([prediction], [reference], lang='en', verbose=False)    
        float_value = round(F1.item(), 4)
        return float_value

    def evaluate_qa_pairs(self, qa_pairs: List[Dict[str, str]]) -> pd.DataFrame:
        """
        Evaluate a list of question-answer pairs and return scores
        """
        results = []
        
        for qa_pair in qa_pairs:
            question = qa_pair['question']
            reference_answer = qa_pair['answer']
            
            # Get RAG response
            rag_response = self.get_rag_response(question).content
            
            # Calculate scores
            rouge_scores = self.calculate_rouge_scores(rag_response, reference_answer)
            bert_score_value = self.calculate_bert_score(rag_response, reference_answer)
            
            # Store results
            result = {
                'question': question,
                'reference_answer': reference_answer,
                'rag_response': rag_response,
                'rouge1_score': round(rouge_scores['rouge1'],4),
                'rougeL_score': round(rouge_scores['rougeL'],4),
                'bert_score': bert_score_value
            }
            self.sqlient.insert_data(result,"rag_evaluation")
            results.append(result)
        
        # Create DataFrame
        df_results = pd.DataFrame(results)
        
        # Add average scores
        averages = {
            'question': 'AVERAGE',
            'reference_answer': '',
            'rag_response': '',
            'rouge1_score': df_results['rouge1_score'].mean(),
            'rougeL_score': df_results['rougeL_score'].mean(),
            'bert_score': df_results['bert_score'].mean()
        }
        df_results = pd.concat([df_results, pd.DataFrame([averages])], ignore_index=True)
        
        return df_results