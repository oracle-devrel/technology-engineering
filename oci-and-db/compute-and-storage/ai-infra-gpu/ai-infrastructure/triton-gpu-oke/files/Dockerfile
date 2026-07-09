FROM <region-key>.ocir.io/<tenancy-namespace>/triton_llm:triton_trt_llm_23.12_manual_build

COPY  output_llama_hf /app/output_llama_hf

COPY model_repo /app/model_repo

RUN mkdir /app/cache
RUN chmod 777 /app/cache