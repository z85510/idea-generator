export type IdeaMetadata = Record<string, string[]>;

export type IdeaGenerationRequest = {
   user_id: string;
   prompt_template: string;
   metadata: IdeaMetadata;
   model?: string;
   temperature?: number;
   number_of_ideas?: number;
};

export type TokenUsage = {
   prompt_tokens: number | null;
   completion_tokens: number | null;
   total_tokens: number | null;
};

export type IdeaGenerationResponse = {
   request_id: string;
   user_id: string;
   prompt_template: string;
   metadata: IdeaMetadata;
   ideas: string[];
   usage: TokenUsage;
   model: string;
   created_at: string;
};

export type WelcomeResponse = {
   message: string;
};
