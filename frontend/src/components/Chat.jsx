import React, {useState, useRef} from "react";
import axios from "axios";
import ResultChart from "./ResultChart";

export default function Chat(){
  const [sessionId] = useState("demo-session");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [chartData, setChartData] = useState(null);
  const loadingRef = useRef(false);

  async function send() {
    if (!input.trim() || loadingRef.current) return;
    const userMsg = {role: "user", content: input};
    setMessages(m => [...m, userMsg]);
    setInput("");
    loadingRef.current = true;

    try {
      const apiBase = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
      const resp = await axios.post(
        `${apiBase}/chat?session_id=${sessionId}`,
        { message: input }
      );
      const text = resp.data.response;
      // optional: if backend returns structured data for charts, get it:
      if (resp.data.chart) {
         setChartData(resp.data.chart);
      } else {
         setChartData(null);
      }
      setMessages(m => [...m, {role:"assistant", content: text}]);
    } catch (e) {
      setMessages(m => [...m, {role:"assistant", content: "Error: " + e.message}]);
    } finally {
      loadingRef.current = false;
    }
  }

  return (
    <div>
      <div className="space-y-3 mb-4 max-h-96 overflow-y-auto p-3 border rounded">
        {messages.map((m,i)=>(
          <div key={i} className={m.role==="user" ? "text-right":"text-left"}>
            <div className={m.role==="user" ? "inline-block bg-blue-500 text-white p-2 rounded":"inline-block bg-gray-100 p-2 rounded"}>
              {m.content}
            </div>
          </div>
        ))}
      </div>

      {chartData && <ResultChart data={chartData} />}

      <div className="flex gap-2">
        <input
          className="flex-1 border rounded p-2"
          value={input}
          onChange={(e)=>setInput(e.target.value)}
          onKeyDown={(e)=> e.key === 'Enter' && send()}
          placeholder="Ask something like: 'Total revenue by region'"
        />
        <button onClick={send} className="px-4 py-2 bg-green-600 text-white rounded">Send</button>
      </div>
    </div>
  );
}