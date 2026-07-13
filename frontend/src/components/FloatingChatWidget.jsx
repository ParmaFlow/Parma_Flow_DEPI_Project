import { useState } from "react";
import { MessageSquare, X, Send, Bot } from "lucide-react";
import { api } from "../api/client";

export function FloatingChatWidget({ token, inventory }) {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    { sender: "ai", text: "Hello! I am your Pharma-Flow AI assistant. How can I help you today?" }
  ]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim() || isTyping) return;
    
    const userMessage = message;
    setChatHistory([...chatHistory, { sender: "user", text: userMessage }]);
    setMessage("");
    setIsTyping(true);
    
    try {
      let invContext = "";
      if (inventory && inventory.length > 0) {
        invContext = "Current Inventory Summary:\n" + inventory.map(item => `- ${item.generic_name} (SKU: ${item.sku_id}): ${item.stock} in stock, forecast demand: ${item.forecast_demand}, expiry in ${item.expiry_days} days.`).join("\n");
      }
      
      const result = await api.chat(token, userMessage, invContext);
      setChatHistory((prev) => [
        ...prev,
        { sender: "ai", text: result.response }
      ]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        { sender: "ai", text: "Error: Could not reach the backend. Please ensure the server is running." }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {isOpen && (
        <div className="mb-4 flex h-96 w-80 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl transition-all duration-300">
          <div className="flex items-center justify-between bg-clinical p-4 text-white">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              <h3 className="font-semibold">AI Assistant</h3>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-white hover:text-blue-200">
              <X className="h-5 w-5" />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
            {chatHistory.map((msg, index) => (
              <div key={index} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-lg p-3 text-sm ${msg.sender === "user" ? "bg-clinical text-white rounded-br-none" : "bg-white border border-slate-200 text-slate-700 rounded-bl-none"}`}>
                  {msg.text}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg p-3 text-sm bg-white border border-slate-200 text-slate-700 rounded-bl-none flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]"></div>
                  <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]"></div>
                  <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400"></div>
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSend} className="border-t border-slate-200 bg-white p-3 flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask anything..."
              className="flex-1 rounded-full border border-slate-300 px-4 py-2 text-sm focus:border-clinical focus:outline-none focus:ring-1 focus:ring-clinical"
            />
            <button type="submit" className="flex h-9 w-9 items-center justify-center rounded-full bg-clinical text-white hover:bg-blue-800 disabled:opacity-50">
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}
      
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-clinical text-white shadow-lg transition-transform hover:scale-105 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-100"
      >
        {isOpen ? <X className="h-6 w-6" /> : <MessageSquare className="h-6 w-6" />}
      </button>
    </div>
  );
}
