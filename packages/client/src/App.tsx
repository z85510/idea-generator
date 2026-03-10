import { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("/api/")
      .then((response) => response.json())
      .then((data) => setMessage(data.message));
  }, []);

  return (
    <div className="text-2xl font-bold text-red-500 p-4 text-center">
      {message}
    </div>
  );
}

export default App;
