import {
   DEFAULT_PROMPT_TEMPLATE,
   DEFAULT_TEMPERATURE,
   DEFAULT_USER_ID,
   EXTRA_INFORMATION_LABEL,
   METADATA_QUESTIONS,
   SUPPORTED_MODELS,
} from './constants';
import type { IdeaGenerationRequest, IdeaMetadata } from './types';

export type MetadataQuestionState = {
   id: string;
   label: string;
   description: string;
   placeholder: string;
   values: string[];
};

export type IdeaGeneratorFormState = {
   apiKey: string;
   userId: string;
   promptTemplate: string;
   model: string;
   temperature: number;
   numberOfIdeas: string;
   extraInformation: string;
   metadataQuestions: MetadataQuestionState[];
};

export function createInitialIdeaGeneratorFormState(): IdeaGeneratorFormState {
   return {
      apiKey: '',
      userId: DEFAULT_USER_ID,
      promptTemplate: DEFAULT_PROMPT_TEMPLATE,
      model: SUPPORTED_MODELS[0]?.value ?? '',
      temperature: DEFAULT_TEMPERATURE,
      numberOfIdeas: '',
      extraInformation: '',
      metadataQuestions: METADATA_QUESTIONS.map((question) => ({
         id: question.id,
         label: question.label,
         description: question.description,
         placeholder: question.placeholder,
         values: [...question.defaultValues],
      })),
   };
}

export function getApiKey(formState: IdeaGeneratorFormState) {
   const apiKey = formState.apiKey.trim();

   if (!apiKey) {
      throw new Error('API key is required.');
   }

   return apiKey;
}

export function normalizeTemperature(value: number) {
   return Math.min(2, Math.max(0, Math.round(value * 10) / 10));
}

export function formatTemperature(value: number) {
   return normalizeTemperature(value).toFixed(1);
}

function sanitizeMetadataValues(values: string[]) {
   return values.map((value) => value.trim()).filter(Boolean);
}

function sanitizeQuestionLabel(value: string) {
   return value.trim();
}

export function toIdeaMetadata(
   metadataQuestions: MetadataQuestionState[],
   extraInformation: string
): IdeaMetadata {
   const entries = metadataQuestions.map((question) => {
      const label = sanitizeQuestionLabel(question.label);
      const values = sanitizeMetadataValues(question.values);

      if (!label) {
         throw new Error('Each question title is required.');
      }

      return [label, values] as const;
   });

   const sanitizedExtraInformation = extraInformation.trim();
   if (sanitizedExtraInformation) {
      entries.push([EXTRA_INFORMATION_LABEL, [sanitizedExtraInformation]]);
   }

   const labels = entries.map(([label]) => label.toLowerCase());
   if (new Set(labels).size !== labels.length) {
      throw new Error('Question titles must be unique.');
   }

   const missingRequiredEntry = entries.find(
      ([, values]) => values.length === 0
   );
   if (missingRequiredEntry) {
      throw new Error(
         `${missingRequiredEntry[0]} requires at least one value.`
      );
   }

   return Object.fromEntries(entries);
}

function parseOptionalInteger(value: string) {
   const trimmedValue = value.trim();

   if (!trimmedValue) {
      return undefined;
   }

   const parsedValue = Number(trimmedValue);
   if (!Number.isInteger(parsedValue) || parsedValue <= 0) {
      throw new Error('Number of ideas must be a positive whole number.');
   }

   return parsedValue;
}

export function toIdeaGenerationRequest(
   formState: IdeaGeneratorFormState
): IdeaGenerationRequest {
   const userId = formState.userId.trim();
   const promptTemplate = formState.promptTemplate.trim();
   const model = formState.model.trim();
   const numberOfIdeas = parseOptionalInteger(formState.numberOfIdeas);

   if (!userId) {
      throw new Error('User ID is required.');
   }

   if (!promptTemplate) {
      throw new Error('Prompt template is required.');
   }

   return {
      user_id: userId,
      prompt_template: promptTemplate,
      metadata: toIdeaMetadata(
         formState.metadataQuestions,
         formState.extraInformation
      ),
      ...(model ? { model } : {}),
      temperature: normalizeTemperature(formState.temperature),
      ...(numberOfIdeas ? { number_of_ideas: numberOfIdeas } : {}),
   };
}
