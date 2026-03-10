import type {
   IdeaGenerationRequest,
   IdeaGenerationResponse,
   WelcomeResponse,
} from './types';

type GenerateIdeasInput = IdeaGenerationRequest & {
   apiKey: string;
};

type ErrorResponse = {
   detail?: string;
};

async function parseErrorMessage(response: Response) {
   try {
      const data = (await response.json()) as ErrorResponse;
      return data.detail || `Request failed with status ${response.status}.`;
   } catch {
      return `Request failed with status ${response.status}.`;
   }
}

export async function fetchWelcomeMessage(): Promise<WelcomeResponse> {
   const response = await fetch('/api/');
   if (!response.ok) {
      throw new Error(await parseErrorMessage(response));
   }

   return (await response.json()) as WelcomeResponse;
}

export async function generateIdeas({
   apiKey,
   ...payload
}: GenerateIdeasInput) {
   const response = await fetch('/api/', {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
         'X-API-Key': apiKey,
      },
      body: JSON.stringify(payload),
   });

   if (!response.ok) {
      throw new Error(await parseErrorMessage(response));
   }

   return (await response.json()) as IdeaGenerationResponse;
}
