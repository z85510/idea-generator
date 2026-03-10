import { useEffect, useState } from 'react';
import { Label } from './components/ui/label';
import { Button } from './components/ui/button';

function App() {
   const [message, setMessage] = useState('');

   useEffect(() => {
      fetch('/api/')
         .then((response) => response.json())
         .then((data) => setMessage(data.message));
   }, []);

   return (
      <div className="flex flex-col items-center justify-center h-screen">
         <Label className="text-2xl font-bold text-red-500 p-4 text-center">
            {message}
         </Label>
         <div className="flex flex-col gap-2">
            <Button variant="outline">Click me (outline)</Button>
            <Button variant="ghost">Click me (ghost)</Button>
            <Button variant="secondary">Click me (secondary)</Button>
            <Button variant="destructive">Click me (destructive)</Button>
            <Button variant="link">Click me (link)</Button>
         </div>
      </div>
   );
}

export default App;
