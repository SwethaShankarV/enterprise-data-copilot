import React from "react";
import Chat from "./components/Chat";
import './index.css';

export default function App(){
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow p-6">
        <h1 className="text-2xl font-semibold mb-4">Enterprise Data Copilot</h1>
        <Chat />
      </div>
    </div>
  );
}