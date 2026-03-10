import {
   Card,
   CardContent,
   CardDescription,
   CardHeader,
   CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

import type { MetadataQuestionState } from '../form';
import { MetadataValuesField } from './metadata-values-field';

type IdeaGenerationQuestionsProps = {
   questions: MetadataQuestionState[];
   extraInformation: string;
   isSubmitting: boolean;
   onExtraInformationChange: (value: string) => void;
   onQuestionLabelChange: (questionId: string, label: string) => void;
   onQuestionValuesChange: (questionId: string, values: string[]) => void;
};

function IdeaGenerationQuestions({
   questions,
   extraInformation,
   isSubmitting,
   onExtraInformationChange,
   onQuestionLabelChange,
   onQuestionValuesChange,
}: IdeaGenerationQuestionsProps) {
   return (
      <Card>
         <CardHeader>
            <CardTitle>Questions</CardTitle>
            <CardDescription>
               Click into any question title to edit it, then add one or more
               answers for each question.
            </CardDescription>
         </CardHeader>
         <CardContent className="grid gap-4">
            {questions.map((question) => (
               <MetadataValuesField
                  key={question.id}
                  question={question}
                  disabled={isSubmitting}
                  onQuestionLabelChange={(label) =>
                     onQuestionLabelChange(question.id, label)
                  }
                  onValuesChange={(values) =>
                     onQuestionValuesChange(question.id, values)
                  }
               />
            ))}

            <Card size="sm" className="gap-3">
               <CardHeader className="gap-2">
                  <CardTitle className="text-base">Extra information</CardTitle>
                  <CardDescription>
                     Add any additional context, constraints, audience notes, or
                     goals that should guide the generated ideas.
                  </CardDescription>
               </CardHeader>
               <CardContent>
                  <div className="grid gap-2">
                     <Label htmlFor="extra-information">Details</Label>
                     <Textarea
                        id="extra-information"
                        value={extraInformation}
                        onChange={(event) =>
                           onExtraInformationChange(event.target.value)
                        }
                        disabled={isSubmitting}
                        placeholder="e.g. I want ideas that can be validated quickly, fit a small team, and target parents in urban areas."
                     />
                  </div>
               </CardContent>
            </Card>
         </CardContent>
      </Card>
   );
}

export { IdeaGenerationQuestions };
