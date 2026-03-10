import { useState, type KeyboardEvent } from 'react';
import {
   Add01Icon,
   Cancel01Icon,
   InformationCircleIcon,
} from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
   Card,
   CardContent,
   CardDescription,
   CardHeader,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

type MetadataValuesFieldProps = {
   question: {
      id: string;
      label: string;
      description: string;
      placeholder: string;
      values: string[];
   };
   disabled?: boolean;
   onQuestionLabelChange: (label: string) => void;
   onValuesChange: (values: string[]) => void;
};

function MetadataValuesField({
   question,
   disabled = false,
   onQuestionLabelChange,
   onValuesChange,
}: MetadataValuesFieldProps) {
   const [draftValue, setDraftValue] = useState('');
   const [draftQuestionLabel, setDraftQuestionLabel] = useState('');
   const [isEditingQuestionLabel, setIsEditingQuestionLabel] = useState(false);
   const values = question.values;

   function appendDraftValues() {
      const nextValues = draftValue
         .split(',')
         .map((value) => value.trim())
         .filter(Boolean);

      if (!nextValues.length) {
         return;
      }

      const mergedValues = [...values];
      for (const nextValue of nextValues) {
         const alreadyIncluded = mergedValues.some(
            (existingValue) =>
               existingValue.toLowerCase() === nextValue.toLowerCase()
         );

         if (!alreadyIncluded) {
            mergedValues.push(nextValue);
         }
      }

      onValuesChange(mergedValues);
      setDraftValue('');
   }

   function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
      if (event.key !== 'Enter') {
         return;
      }

      event.preventDefault();
      appendDraftValues();
   }

   function removeValue(valueToRemove: string) {
      onValuesChange(values.filter((value) => value !== valueToRemove));
   }

   function startQuestionLabelEditing() {
      if (disabled) {
         return;
      }

      setDraftQuestionLabel(question.label);
      setIsEditingQuestionLabel(true);
   }

   function commitQuestionLabel() {
      onQuestionLabelChange(draftQuestionLabel.trim());
      setIsEditingQuestionLabel(false);
   }

   function cancelQuestionLabelEditing() {
      setDraftQuestionLabel(question.label);
      setIsEditingQuestionLabel(false);
   }

   function handleQuestionLabelKeyDown(event: KeyboardEvent<HTMLInputElement>) {
      if (event.key === 'Enter') {
         event.preventDefault();
         commitQuestionLabel();
      }

      if (event.key === 'Escape') {
         event.preventDefault();
         cancelQuestionLabelEditing();
      }
   }

   return (
      <Card size="sm" className="gap-3">
         <CardHeader className="gap-2">
            <div className="flex items-start justify-between gap-3">
               <div className="grid flex-1 gap-2">
                  {isEditingQuestionLabel ? (
                     <Input
                        id={`${question.id}-label`}
                        value={draftQuestionLabel}
                        onChange={(event) =>
                           setDraftQuestionLabel(event.target.value)
                        }
                        onBlur={commitQuestionLabel}
                        onKeyDown={handleQuestionLabelKeyDown}
                        disabled={disabled}
                        autoFocus
                        className="h-auto border-transparent bg-transparent px-0 py-0 text-base font-semibold shadow-none focus-visible:border-ring/50"
                     />
                  ) : (
                     <Button
                        type="button"
                        variant="ghost"
                        onClick={startQuestionLabelEditing}
                        disabled={disabled}
                        className="h-auto justify-start px-0 py-0 text-left text-base font-semibold text-foreground hover:bg-transparent"
                     >
                        {question.label || 'Untitled question'}
                     </Button>
                  )}
               </div>
            </div>
         </CardHeader>
         <CardContent className="grid gap-3">
            <div className="flex flex-col gap-2 sm:flex-row">
               <Input
                  id={`${question.id}-input`}
                  value={draftValue}
                  onChange={(event) => setDraftValue(event.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={question.placeholder}
                  disabled={disabled}
               />
               <Button
                  type="button"
                  variant="secondary"
                  onClick={appendDraftValues}
                  disabled={disabled || !draftValue.trim()}
               >
                  <HugeiconsIcon icon={Add01Icon} />
                  Add
               </Button>
            </div>

            {values.length ? (
               <div className="flex flex-wrap gap-2">
                  {values.map((value) => (
                     <div
                        key={`${question.id}-${value}`}
                        className="flex items-center gap-1 bg-muted rounded-md px-2 py-1"
                     >
                        <Badge variant="secondary" className="h-auto px-2 py-1">
                           {value}
                        </Badge>
                        <Button
                           type="button"
                           variant="outline"
                           size="icon-xs"
                           aria-label={`Remove ${value}`}
                           disabled={disabled}
                           onClick={() => removeValue(value)}
                        >
                           <HugeiconsIcon icon={Cancel01Icon} />
                        </Button>
                     </div>
                  ))}
               </div>
            ) : (
               <Alert>
                  <HugeiconsIcon icon={InformationCircleIcon} />
                  <AlertTitle>Add at least one value</AlertTitle>
                  <AlertDescription>
                     Press Enter or use the Add button to save each item.
                  </AlertDescription>
               </Alert>
            )}
         </CardContent>
      </Card>
   );
}

export { MetadataValuesField };
