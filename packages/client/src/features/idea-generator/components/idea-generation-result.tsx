import { InformationCircleIcon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
   Card,
   CardAction,
   CardContent,
   CardDescription,
   CardHeader,
   CardTitle,
} from '@/components/ui/card';

import type { IdeaGenerationResponse } from '../types';

type IdeaGenerationResultProps = {
   result: IdeaGenerationResponse | null;
   isSubmitting: boolean;
};

function formatTimestamp(value: string) {
   const date = new Date(value);

   if (Number.isNaN(date.getTime())) {
      return value;
   }

   return date.toLocaleString();
}

function usageValue(value: number | null) {
   return value ?? '—';
}

function IdeaGenerationResult({
   result,
   isSubmitting,
}: IdeaGenerationResultProps) {
   if (!result) {
      return (
         <Card>
            <CardHeader>
               <CardTitle>Generated ideas</CardTitle>
               <CardDescription>
                  {isSubmitting
                     ? 'Generating ideas and waiting for the API response.'
                     : 'Submit the form to see generated ideas, model details, and token usage.'}
               </CardDescription>
            </CardHeader>
         </Card>
      );
   }

   return (
      <div className="grid gap-4">
         <Alert>
            <HugeiconsIcon icon={InformationCircleIcon} />
            <AlertTitle>Ideas generated successfully</AlertTitle>
            <AlertDescription>
               Request {result.request_id} completed with {result.model}.
            </AlertDescription>
         </Alert>

         <Card>
            <CardHeader>
               <CardTitle>Generated ideas</CardTitle>
               <CardDescription>
                  Created at {formatTimestamp(result.created_at)}
               </CardDescription>
               <CardAction>
                  <Badge variant="secondary">{result.ideas.length} ideas</Badge>
               </CardAction>
            </CardHeader>
            <CardContent className="grid gap-4">
               <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">
                     Request ID: {result.request_id}
                  </Badge>
                  <Badge variant="outline">Model: {result.model}</Badge>
                  <Badge variant="outline">User: {result.user_id}</Badge>
               </div>

               <div className="grid gap-3">
                  {result.ideas.map((idea, index) => (
                     <Card key={`${result.request_id}-${index}`} size="sm">
                        <CardContent className="grid gap-2 py-3">
                           <Badge variant="secondary">Idea {index + 1}</Badge>
                           <div>{idea}</div>
                        </CardContent>
                     </Card>
                  ))}
               </div>

               <div className="grid gap-3 md:grid-cols-3">
                  <Card size="sm">
                     <CardHeader>
                        <CardTitle>Prompt tokens</CardTitle>
                     </CardHeader>
                     <CardContent>
                        {usageValue(result.usage.prompt_tokens)}
                     </CardContent>
                  </Card>
                  <Card size="sm">
                     <CardHeader>
                        <CardTitle>Completion tokens</CardTitle>
                     </CardHeader>
                     <CardContent>
                        {usageValue(result.usage.completion_tokens)}
                     </CardContent>
                  </Card>
                  <Card size="sm">
                     <CardHeader>
                        <CardTitle>Total tokens</CardTitle>
                     </CardHeader>
                     <CardContent>
                        {usageValue(result.usage.total_tokens)}
                     </CardContent>
                  </Card>
               </div>
            </CardContent>
         </Card>
      </div>
   );
}

export { IdeaGenerationResult };
