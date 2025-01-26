import React, { useState } from 'react';
import axios from 'axios';
import './Chatbox.css';

function Chatbox() {
    const [messages, setMessages] = useState([]);
    const [query, setQuery] = useState("");
    const [isSending, setIsSending] = useState(false); // To track if a request is in progress

    const handleSend = async () => {
        if (query.trim() === "" || isSending) return; // Prevent sending if already sending or query is empty
        console.log('Sending query:', query);  // Add console logging to track

        // Set sending status to true to prevent multiple requests
        setIsSending(true);

        const userMessage = { sender: "user", text: query };
        setMessages((prevMessages) => [...prevMessages, userMessage]);

        try {
            const response = await axios.post("http://127.0.0.1:5000/ask", { query });
            console.log("Response:", response); // Log response for debugging

            const botMessageText = response.data.answer || "No response from bot.";
            const botMessage = { sender: "bot", text: botMessageText };
            setMessages((prevMessages) => [...prevMessages, botMessage]);
        } catch (error) {
            console.error(error);
            const errorMessage = { sender: "bot", text: "Error: Unable to fetch data." };
            setMessages((prevMessages) => [...prevMessages, errorMessage]);
        }

        // Reset query and sending status
        setQuery("");
        setIsSending(false);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission if Enter key is pressed
            handleSend();
        }
    };

    return (
        <div className="chatbox">
            <div className="chat-history">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender}`}>
                        {msg.text}
                    </div>
                ))}
            </div>
            <div className="chat-input">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={handleKeyPress}  // Handle Enter key press
                    placeholder="Type your query..."
                />
                <button onClick={handleSend} disabled={isSending}>Send</button> {/* Disable button while sending */}
            </div>
        </div>
    );
}

export default Chatbox;
