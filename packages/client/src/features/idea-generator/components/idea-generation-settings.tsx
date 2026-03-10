import { Alert01Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
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
import {
   Select,
   SelectContent,
   SelectItem,
   SelectTrigger,
   SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Textarea } from '@/components/ui/textarea';

import { SUPPORTED_MODELS } from '../constants';
import { formatTemperature, type IdeaGeneratorFormState } from '../form';

type IdeaGenerationSettingsProps = {
   formState: IdeaGeneratorFormState;
   errorMessage: string;
   isSubmitting: boolean;
   onFieldChange: (
      field: 'apiKey' | 'userId' | 'promptTemplate' | 'model' | 'numberOfIdeas',
      value: string
   ) => void;
   onTemperatureChange: (value: number) => void;
};

function IdeaGenerationSettings({
   formState,
   errorMessage,
   isSubmitting,
   onFieldChange,
   onTemperatureChange,
}: IdeaGenerationSettingsProps) {
   const selectedModel = SUPPORTED_MODELS.find(
      (model) => model.value === formState.model
   );

   return (
      <Card className="xl:sticky xl:top-8">
         <CardHeader>
            <CardTitle>Settings</CardTitle>
            <CardDescription>
               Configure access, model behavior, and request options before
               generating ideas.
            </CardDescription>
         </CardHeader>
         <CardContent className="grid gap-6">
            <div className="grid gap-4">
               <div className="grid gap-2">
                  <Label htmlFor="api-key">API key</Label>
                  <Input
                     id="api-key"
                     type="password"
                     autoComplete="off"
                     value={formState.apiKey}
                     onChange={(event) =>
                        onFieldChange('apiKey', event.target.value)
                     }
                     placeholder="Enter the X-API-Key value"
                     disabled={isSubmitting}
                  />
               </div>
               <div className="grid gap-2">
                  <Label htmlFor="user-id">User ID</Label>
                  <Input
                     id="user-id"
                     value={formState.userId}
                     onChange={(event) =>
                        onFieldChange('userId', event.target.value)
                     }
                     placeholder="user-1"
                     disabled={isSubmitting}
                  />
               </div>
            </div>

            <div className="grid gap-4">
               <div className="grid gap-2">
                  <Label htmlFor="model">Model</Label>
                  <Select
                     value={formState.model}
                     onValueChange={(value) => onFieldChange('model', value)}
                     disabled={isSubmitting}
                  >
                     <SelectTrigger id="model" className="w-full">
                        <SelectValue placeholder="Select a model" />
                     </SelectTrigger>
                     <SelectContent>
                        {SUPPORTED_MODELS.map((model) => (
                           <SelectItem key={model.value} value={model.value}>
                              <span className="flex flex-col items-start gap-0.5">
                                 <span>{model.label}</span>
                                 <span className="text-xs text-muted-foreground">
                                    {model.value}
                                 </span>
                              </span>
                           </SelectItem>
                        ))}
                     </SelectContent>
                  </Select>
                  {selectedModel ? (
                     <CardDescription>
                        {selectedModel.description}
                     </CardDescription>
                  ) : null}
               </div>

               <div className="grid gap-2">
                  <Label htmlFor="number-of-ideas">Number of ideas</Label>
                  <Input
                     id="number-of-ideas"
                     type="number"
                     min="1"
                     max="20"
                     value={formState.numberOfIdeas}
                     onChange={(event) =>
                        onFieldChange('numberOfIdeas', event.target.value)
                     }
                     placeholder="Use server default"
                     disabled={isSubmitting}
                  />
               </div>

               <div className="grid gap-3">
                  <div className="flex items-center justify-between gap-3">
                     <div className="grid gap-1">
                        <Label>Temperature</Label>
                        <CardDescription>
                           Lower values stay focused. Higher values explore
                           more.
                        </CardDescription>
                     </div>
                     <Badge variant="outline">
                        {formatTemperature(formState.temperature)}
                     </Badge>
                  </div>
                  <Slider
                     aria-label="Temperature"
                     min={0}
                     max={2}
                     step={0.1}
                     value={[formState.temperature]}
                     onValueChange={(value) =>
                        onTemperatureChange(value[0] ?? formState.temperature)
                     }
                     disabled={isSubmitting}
                  />
               </div>
            </div>

            <div className="grid gap-2">
               <Label htmlFor="prompt-template">Prompt template</Label>
               <Textarea
                  id="prompt-template"
                  value={formState.promptTemplate}
                  onChange={(event) =>
                     onFieldChange('promptTemplate', event.target.value)
                  }
                  placeholder="Describe how the backend should frame the generated ideas."
                  disabled={isSubmitting}
               />
            </div>

            {errorMessage ? (
               <Alert variant="destructive">
                  <HugeiconsIcon icon={Alert01Icon} />
                  <AlertTitle>Unable to generate ideas</AlertTitle>
                  <AlertDescription>{errorMessage}</AlertDescription>
               </Alert>
            ) : null}
         </CardContent>
         <CardFooter className="justify-end">
            <Button type="submit" disabled={isSubmitting}>
               {isSubmitting ? 'Generating ideas...' : 'Generate ideas'}
            </Button>
         </CardFooter>
      </Card>
   );
}

export { IdeaGenerationSettings };
