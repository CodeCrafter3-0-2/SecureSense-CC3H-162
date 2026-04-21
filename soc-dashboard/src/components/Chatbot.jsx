import { useState } from "react";

const API = "http://192.168.16.74:8000";

export default function Chatbot() {
  const [q, setQ] = useState("");
  const [res, setRes] = useState("");

  const ask = async () => {
    setRes("Analyzing...");
    const r = await fetch(`${API}/chat`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ question: q })
    });

    const data = await r.json();
    setRes(data.response);
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg border border-purple-500/30 p-4 rounded-xl shadow-xl">
      <h2 className="text-purple-400 mb-2">🤖 SOC Assistant</h2>

      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        className="w-full p-2 mb-2 bg-black border border-white/10 rounded"
        placeholder="Ask threat insights..."
      />

      <button
        onClick={ask}
        className="w-full bg-purple-500 p-2 rounded"
      >
        Analyze
      </button>

      <p className="text-sm mt-2 text-gray-300">{res}</p>
    </div>
  );
}