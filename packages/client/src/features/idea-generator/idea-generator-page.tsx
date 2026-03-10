import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react';

import { Button } from '@/components/ui/button';
import {
   Card,
   CardContent,
   CardDescription,
   CardFooter,
   CardHeader,
   CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

import { fetchWelcomeMessage, generateIdeas } from './api';
import type {
   IdeaGenerationRequest,
   IdeaGenerationResponse,
   IdeaMetadata,
} from './types';

const defaultMetadataJson = JSON.stringify(
   {
      'What do you love': ['tech', 'art'],
      'What does the world need': ['education'],
      'What are you good at': ['design', 'coding'],
      'Extra information': ['I enjoy building practical products.'],
   },
   null,
   2
);

type FormState = {
   apiKey: string;
   userId: string;
   promptTemplate: string;
   metadataJson: string;
   model: string;
   temperature: string;
   numberOfIdeas: string;
};

const initialFormState: FormState = {
   apiKey: '',
   userId: 'user-1',
   promptTemplate: 'You generate practical and creative project ideas.',
   metadataJson: defaultMetadataJson,
   model: '',
   temperature: '',
   numberOfIdeas: '',
};

function parseMetadataJson(metadataJson: string): IdeaMetadata {
   const parsed: unknown = JSON.parse(metadataJson);

   if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error(
         'Metadata must be a JSON object with string-array values.'
      );
   }

   for (const [key, value] of Object.entries(
      parsed as Record<string, unknown>
   )) {
      if (
         !key.trim() ||
         !Array.isArray(value) ||
         !value.every((item) => typeof item === 'string')
      ) {
         throw new Error(
            'Each metadata field must contain an array of strings.'
         );
      }
   }

   return parsed as IdeaMetadata;
}

function parseOptionalNumber(value: string) {
   if (!value.trim()) {
      return undefined;
   }

   const parsed = Number(value);
   if (Number.isNaN(parsed)) {
      throw new Error('Numeric fields must contain valid numbers.');
   }

   return parsed;
}

function parseOptionalInteger(value: string) {
   const parsed = parseOptionalNumber(value);
   if (parsed === undefined) {
      return undefined;
   }
   if (!Number.isInteger(parsed)) {
      throw new Error('Number of ideas must be a whole number.');
   }

   return parsed;
}

function IdeaGeneratorPage() {
   const [welcomeMessage, setWelcomeMessage] = useState('Idea Generator');
   const [formState, setFormState] = useState<FormState>(initialFormState);
   const [result, setResult] = useState<IdeaGenerationResponse | null>(null);
   const [errorMessage, setErrorMessage] = useState('');
   const [isSubmitting, setIsSubmitting] = useState(false);

   useEffect(() => {
      let isMounted = true;

      fetchWelcomeMessage()
         .then((response) => {
            if (isMounted) {
               setWelcomeMessage(response.message);
            }
         })
         .catch(() => {
            if (isMounted) {
               setWelcomeMessage('Idea Generator');
            }
         });

      return () => {
         isMounted = false;
      };
   }, []);

   function handleFieldChange(field: keyof FormState) {
      return (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
         setFormState((current) => ({
            ...current,
            [field]: event.target.value,
         }));
      };
   }

   async function handleSubmit(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      setErrorMessage('');
      setIsSubmitting(true);

      try {
         if (!formState.apiKey.trim()) {
            throw new Error('API key is required.');
         }
         if (!formState.userId.trim()) {
            throw new Error('User ID is required.');
         }
         if (!formState.promptTemplate.trim()) {
            throw new Error('Prompt template is required.');
         }

         const requestPayload: IdeaGenerationRequest = {
            user_id: formState.userId.trim(),
            prompt_template: formState.promptTemplate.trim(),
            metadata: parseMetadataJson(formState.metadataJson),
            ...(formState.model.trim()
               ? { model: formState.model.trim() }
               : {}),
            ...(formState.temperature.trim()
               ? { temperature: parseOptionalNumber(formState.temperature) }
               : {}),
            ...(formState.numberOfIdeas.trim()
               ? {
                    number_of_ideas: parseOptionalInteger(
                       formState.numberOfIdeas
                    ),
                 }
               : {}),
         };

         const response = await generateIdeas({
            apiKey: formState.apiKey.trim(),
            ...requestPayload,
         });

         setResult(response);
      } catch (error) {
         setErrorMessage(
            error instanceof Error ? error.message : 'Something went wrong.'
         );
      } finally {
         setIsSubmitting(false);
      }
   }

   return (
      <main className="min-h-screen bg-background px-4 py-8 text-foreground">
         <div className="mx-auto flex max-w-6xl flex-col gap-6">
            <Card>
               <CardHeader>
                  <CardTitle>{welcomeMessage}</CardTitle>
                  <CardDescription>
                     Send idea-generation requests with optional model,
                     temperature, and idea-count overrides.
                  </CardDescription>
               </CardHeader>
            </Card>

            <Card>
               <CardHeader>
                  <CardTitle>Generate ideas</CardTitle>
                  <CardDescription>
                     Leave optional fields empty to use the server defaults.
                  </CardDescription>
               </CardHeader>
               <form onSubmit={handleSubmit}>
                  <CardContent className="grid gap-4 md:grid-cols-2">
                     <div className="grid gap-2">
                        <Label htmlFor="api-key">API key</Label>
                        <Input
                           id="api-key"
                           type="password"
                           value={formState.apiKey}
                           onChange={handleFieldChange('apiKey')}
                        />
                     </div>
                     <div className="grid gap-2">
                        <Label htmlFor="user-id">User ID</Label>
                        <Input
                           id="user-id"
                           value={formState.userId}
                           onChange={handleFieldChange('userId')}
                        />
                     </div>
                     <div className="grid gap-2 md:col-span-2">
                        <Label htmlFor="prompt-template">Prompt template</Label>
                        <Textarea
                           id="prompt-template"
                           value={formState.promptTemplate}
                           onChange={handleFieldChange('promptTemplate')}
                        />
                     </div>
                     <div className="grid gap-2">
                        <Label htmlFor="model">Model (optional)</Label>
                        <Input
                           id="model"
                           value={formState.model}
                           onChange={handleFieldChange('model')}
                           placeholder="openai/gpt-4o-mini"
                        />
                     </div>
                     <div className="grid gap-2">
                        <Label htmlFor="temperature">
                           Temperature (optional)
                        </Label>
                        <Input
                           id="temperature"
                           type="number"
                           step="0.1"
                           min="0"
                           max="2"
                           value={formState.temperature}
                           onChange={handleFieldChange('temperature')}
                           placeholder="0.9"
                        />
                     </div>
                     <div className="grid gap-2 md:col-span-2">
                        <Label htmlFor="number-of-ideas">
                           Number of ideas (optional)
                        </Label>
                        <Input
                           id="number-of-ideas"
                           type="number"
                           min="1"
                           max="20"
                           value={formState.numberOfIdeas}
                           onChange={handleFieldChange('numberOfIdeas')}
                           placeholder="5"
                        />
                     </div>
                     <div className="grid gap-2 md:col-span-2">
                        <Label htmlFor="metadata-json">Metadata JSON</Label>
                        <Textarea
                           id="metadata-json"
                           value={formState.metadataJson}
                           onChange={handleFieldChange('metadataJson')}
                           className="min-h-64 font-mono text-xs"
                        />
                     </div>
                     {errorMessage ? (
                        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive md:col-span-2">
                           {errorMessage}
                        </div>
                     ) : null}
                  </CardContent>
                  <CardFooter className="justify-end">
                     <Button type="submit" disabled={isSubmitting}>
                        {isSubmitting ? 'Generating...' : 'Generate ideas'}
                     </Button>
                  </CardFooter>
               </form>
            </Card>

            {result ? (
               <Card>
                  <CardHeader>
                     <CardTitle>Generated ideas</CardTitle>
                     <CardDescription>
                        Model: {result.model} • Request ID: {result.request_id}
                     </CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-4">
                     <div className="grid gap-2">
                        {result.ideas.map((idea, index) => (
                           <div
                              key={`${result.request_id}-${index}`}
                              className="rounded-lg border bg-muted/30 px-3 py-2 text-sm"
                           >
                              <span className="font-medium">
                                 Idea {index + 1}:
                              </span>{' '}
                              {idea}
                           </div>
                        ))}
                     </div>
                     <div className="grid gap-1 text-sm text-muted-foreground">
                        <div>
                           Prompt tokens: {result.usage.prompt_tokens ?? '—'}
                        </div>
                        <div>
                           Completion tokens:{' '}
                           {result.usage.completion_tokens ?? '—'}
                        </div>
                        <div>
                           Total tokens: {result.usage.total_tokens ?? '—'}
                        </div>
                     </div>
                  </CardContent>
               </Card>
            ) : null}
         </div>
      </main>
   );
}

export default IdeaGeneratorPage;
