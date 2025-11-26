#!/usr/bin/env python3
"""Complete the vLLM migration for modal-rag.py"""

import re

# Read the file
with open('modal-rag-new.py', 'r') as f:
    content = f.read()

# 1. Remove duplicate vllm line
content = content.replace(
    '        "vllm==0.6.3.post1",  # Fast inference engine\n        "vllm==0.6.3.post1",  # Fast inference engine\n',
    '        "vllm==0.6.3.post1",  # Fast inference engine\n'
)

# 2. Remove accelerate, sentencepiece, protobuf (not needed with vLLM)
content = re.sub(r'\s+"accelerate==1\.1\.1",\n', '', content)
content = re.sub(r'\s+"sentencepiece==0\.2\.0",.*\n', '', content)
content = re.sub(r'\s+"protobuf==5\.29\.2".*\n', '', content)

# 3. Replace the LLM loading section (from "print("🤖 Loading LLM model...")" to "print("✅ Model loaded and ready!")")
old_llm_section = r'''        print\("🤖 Loading LLM model..."\)
        self\.tokenizer = AutoTokenizer\.from_pretrained\(
            LLM_MODEL,
            use_fast=True
        \)
        self\.model = AutoModelForCausalLM\.from_pretrained\(
            LLM_MODEL,
            torch_dtype=torch\.float16,
            device_map="auto"
        \)
        
        pipe = pipeline\(
            "text-generation",
            model=self\.model,
            tokenizer=self\.tokenizer,
            max_new_tokens=512,
            temperature=0\.1,
            do_sample=True
        \)
        
        self\.llm = HuggingFacePipeline\(pipeline=pipe\)
        print\("✅ Model loaded and ready!"\)'''

new_llm_section = '''        print("🤖 Loading vLLM...")
        from vllm import LLM, SamplingParams
        
        self.llm_engine = LLM(
            model=LLM_MODEL,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.85,
            max_model_len=4096,
            trust_remote_code=True
        )
        
        self.sampling_params = SamplingParams(
            temperature=0.7,
            max_tokens=256,
            top_p=0.9,
            stop=["<|end|>"]
        )
        
        print("✅ vLLM ready!")'''

content = re.sub(old_llm_section, new_llm_section, content)

# 4. Replace the query method (from "@modal.method()" to the return statement)
old_query_section = r'''    @modal\.method\(\)
    def query\(self, question: str, top_k: int = 3\):
        from langchain\.chains import RetrievalQA
        
        print\(f"❓ Query: \{question\}"\)
        
        retriever = self\.RemoteChromaRetriever\(
            chroma_service=self\.chroma_service,
            embeddings=self\.embeddings,
            k=top_k
        \)
        
        print\("⚙️ Creating RAG chain..."\)
        qa_chain = RetrievalQA\.from_chain_type\(
            llm=self\.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        \)
        
        print\("🔎 Searching and generating answer..."\)
        result = qa_chain\.invoke\(\{"query": question\}\)
        
        return \{
            "question": question,
            "answer": result\["result"\],
            "sources": \[
                \{
                    "content": doc\.page_content\[:300\],
                    "metadata": doc\.metadata
                \}
                for doc in result\["source_documents"\]
            \]
        \}'''

new_query_section = '''    @modal.method()
    def query(self, question: str, top_k: int = 2):
        import time
        start = time.time()
        
        print(f"❓ {question}")
        
        retriever = self.RemoteChromaRetriever(
            chroma_service=self.chroma_service,
            embeddings=self.embeddings,
            k=top_k
        )
        docs = retriever.get_relevant_documents(question)
        retrieval_time = time.time() - start
        
        context = "\\n\\n".join([doc.page_content for doc in docs])
        
        prompt = f"""<|system|>
You are a helpful AI assistant. Answer questions about insurance products based on the context. Be concise.<|end|>
