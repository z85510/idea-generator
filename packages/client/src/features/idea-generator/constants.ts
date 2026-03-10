export const DEFAULT_USER_ID = 'user-1';
export const DEFAULT_PROMPT_TEMPLATE =
   'You generate practical and creative project ideas.';
export const DEFAULT_TEMPERATURE = 0.9;
export const EXTRA_INFORMATION_LABEL = 'Extra information';

export const SUPPORTED_MODELS = [
   {
      label: 'OpenAI GPT-4o Mini',
      value: 'openai/gpt-4o-mini',
   },
   {
      label: 'OpenAI GPT-4.1 Mini',
      value: 'openai/gpt-4.1-mini',
   },
   {
      label: 'Anthropic Claude Haiku 4.5',
      value: 'anthropic/claude-haiku-4.5',
   },
   {
      label: 'Anthropic Claude Sonnet 4',
      value: 'anthropic/claude-sonnet-4',
   },
   {
      label: 'Google Gemini 2.0 Flash',
      value: 'google/gemini-2.0-flash-001',
   },
   {
      label: 'Meta Llama 3.3 70B Instruct',
      value: 'meta-llama/llama-3.3-70b-instruct',
   },
] as const;

export const METADATA_QUESTIONS = [
   {
      id: 'love',
      label: 'What do you love',
      description:
         'Add industries, topics, problems, or communities you care about.',
      placeholder: 'e.g. education, local communities, AI tools',
      defaultValues: ['technology', 'design'],
   },
   {
      id: 'world-need',
      label: 'What does the world need',
      description: 'Capture real needs, pains, or opportunities worth solving.',
      placeholder: 'e.g. better mental health support, affordable learning',
      defaultValues: ['education'],
   },
   {
      id: 'strengths',
      label: 'What are you good at',
      description:
         'List strengths, skills, or experiences you can realistically use.',
      placeholder: 'e.g. product design, coding, storytelling',
      defaultValues: ['product strategy', 'software development'],
   },
] as const;
