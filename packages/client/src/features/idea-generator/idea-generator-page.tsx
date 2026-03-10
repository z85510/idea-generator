import { useEffect, useState, type FormEvent } from 'react';

import { Badge } from '@/components/ui/badge';
import {
   Card,
   CardDescription,
   CardHeader,
   CardTitle,
} from '@/components/ui/card';

import { fetchWelcomeMessage, generateIdeas } from './api';
import { SUPPORTED_MODELS } from './constants';
import { IdeaGenerationQuestions } from './components/idea-generation-questions';
import { IdeaGenerationSettings } from './components/idea-generation-settings';
import {
   createInitialIdeaGeneratorFormState,
   getApiKey,
   normalizeTemperature,
   toIdeaGenerationRequest,
} from './form';
import { IdeaGenerationResult } from './components/idea-generation-result';
import type { IdeaGenerationResponse } from './types';

function IdeaGeneratorPage() {
   const [welcomeMessage, setWelcomeMessage] = useState('Idea Generator');
   const [formState, setFormState] = useState(
      createInitialIdeaGeneratorFormState
   );
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

   function handleFieldChange(
      field:
         | 'apiKey'
         | 'userId'
         | 'promptTemplate'
         | 'model'
         | 'numberOfIdeas'
         | 'extraInformation',
      value: string
   ) {
      setFormState((current) => ({
         ...current,
         [field]: value,
      }));
   }

   function handleTemperatureChange(value: number) {
      setFormState((current) => ({
         ...current,
         temperature: normalizeTemperature(value),
      }));
   }

   function handleQuestionLabelChange(questionId: string, label: string) {
      setFormState((current) => ({
         ...current,
         metadataQuestions: current.metadataQuestions.map((question) =>
            question.id === questionId ? { ...question, label } : question
         ),
      }));
   }

   function handleQuestionValuesChange(questionId: string, values: string[]) {
      setFormState((current) => ({
         ...current,
         metadataQuestions: current.metadataQuestions.map((question) =>
            question.id === questionId ? { ...question, values } : question
         ),
      }));
   }

   async function handleSubmit(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      setErrorMessage('');
      setIsSubmitting(true);

      try {
         const response = await generateIdeas({
            apiKey: getApiKey(formState),
            ...toIdeaGenerationRequest(formState),
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
         <div className="mx-auto flex max-w-7xl flex-col gap-6">
            <Card>
               <CardHeader>
                  <CardTitle>{welcomeMessage}</CardTitle>
                  <CardDescription>
                     Generate structured ideas with a selected model, a tuned
                     temperature, and metadata captured through dedicated UI
                     fields.
                  </CardDescription>
                  <div className="flex flex-wrap gap-2 pt-2">
                     {SUPPORTED_MODELS.map((model) => (
                        <Badge key={model.value} variant="outline">
                           {model.label}
                        </Badge>
                     ))}
                  </div>
               </CardHeader>
            </Card>

            <div className="grid gap-6 xl:grid-cols-3 xl:items-start">
               <form
                  onSubmit={handleSubmit}
                  className="grid gap-6 xl:col-span-2 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] xl:items-start"
               >
                  <IdeaGenerationSettings
                     formState={formState}
                     errorMessage={errorMessage}
                     isSubmitting={isSubmitting}
                     onFieldChange={handleFieldChange}
                     onTemperatureChange={handleTemperatureChange}
                  />
                  <IdeaGenerationQuestions
                     questions={formState.metadataQuestions}
                     extraInformation={formState.extraInformation}
                     isSubmitting={isSubmitting}
                     onExtraInformationChange={(value) =>
                        handleFieldChange('extraInformation', value)
                     }
                     onQuestionLabelChange={handleQuestionLabelChange}
                     onQuestionValuesChange={handleQuestionValuesChange}
                  />
               </form>
               <div className="xl:sticky xl:top-8">
                  <IdeaGenerationResult
                     result={result}
                     isSubmitting={isSubmitting}
                  />
               </div>
            </div>
         </div>
      </main>
   );
}

export default IdeaGeneratorPage;
