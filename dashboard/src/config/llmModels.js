export const LLM_PROVIDER = 'llama.cpp';

export const AVAILABLE_LLM_MODELS = [
  {
    id: 'unsloth/gemma-4-E2B-it-qat-GGUF:UD-Q4_K_XL',
    name: 'Gemma 4 E2B QAT',
    provider: 'Unsloth GGUF',
    description: 'Smallest Unsloth QAT dynamic Q4 option for quick local insight generation.',
    size: '2.62 GB',
    speed: 'Very fast',
    recommended: false
  },
  {
    id: 'unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL',
    name: 'Gemma 4 E4B',
    provider: 'Unsloth GGUF',
    description: 'Default Unsloth dynamic Q4 model. Good balance for structured JSON summaries.',
    size: '~5 GB',
    speed: 'Fast',
    recommended: true
  },
  {
    id: 'unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M',
    name: 'Gemma 4 26B A4B',
    provider: 'Unsloth GGUF',
    description: 'MoE Unsloth dynamic Q4 option for stronger local analysis on larger machines.',
    size: '~16.9 GB',
    speed: 'Moderate',
    recommended: false
  },
  {
    id: 'unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL',
    name: 'Gemma 4 31B',
    provider: 'Unsloth GGUF',
    description: 'Largest Unsloth dynamic Q4 option for best quality when memory is available.',
    size: '18.8 GB',
    speed: 'Slow',
    recommended: false
  }
];
