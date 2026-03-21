'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, User, Bot, Globe, Sparkles, Heart, MessageCircle, Mic } from 'lucide-react';
import { chatApi, knowledgeApi } from '@/services/api';
import { ChatRequest, ChatResponse, PersonalProfile } from '@/services/api';
import toast, { Toaster } from 'react-hot-toast';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
}


export default function AgentInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [language] = useState<'en'>('en');
  const [showProfile, setShowProfile] = useState(false);
  const [profile, setProfile] = useState<PersonalProfile | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const newSessionId = `session_${Date.now()}`;
    setSessionId(newSessionId);
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const profileData = await knowledgeApi.getProfile();
      setProfile(profileData);
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const request: ChatRequest = {
        message: input,
        session_id: sessionId,
        language,
      };

      const response: ChatResponse = await chatApi.sendMessage(request);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        sources: response.sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      toast.error('Failed to send message. Please try again.');
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };


  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    setIsTyping(true);
    
    // Auto-resize textarea
    const target = e.target;
    target.style.height = 'auto';
    target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
    
    // Reset typing indicator after delay
    setTimeout(() => setIsTyping(false), 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 via-gray-50 to-gray-100">
      <Toaster position="top-right" toastOptions={{
        style: {
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(0, 0, 0, 0.05)',
          borderRadius: '12px',
        },
      }} />
      
      {/* Header */}
      <header className="border-b border-gray-200/80 backdrop-blur-xl bg-white/90">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-4"
            >
              <div className="relative">
                <motion.div 
                  animate={{ rotate: 360 }}
                  transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                  className="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 rounded-2xl blur-lg opacity-20"
                ></motion.div>
                <div className="relative bg-gradient-to-r from-purple-500 to-pink-500 p-3 rounded-2xl shadow-md">
                  <Heart className="w-6 h-6 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Assaf Azran
                </h1>
                <p className="text-gray-600 text-sm">Personal AI Agent</p>
              </div>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-3"
            >
              <div className="flex items-center space-x-2 px-3 py-1.5 bg-purple-50 rounded-lg border border-purple-100">
                <Globe className="w-4 h-4 text-purple-600" />
                <span className="text-purple-700 text-xs font-medium">
                  English UI • Hebrew supported
                </span>
              </div>
              
              <button
                onClick={() => setShowProfile(!showProfile)}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all duration-200 group"
              >
                <User className="w-4 h-4 text-gray-600 group-hover:text-purple-600 transition-colors" />
                <span className="text-gray-700 text-sm font-medium group-hover:text-purple-600 transition-colors">
                  Profile
                </span>
              </button>
            </motion.div>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Sidebar */}
        <aside className="w-80 border-r border-gray-200/80 bg-white/70 backdrop-blur-xl">
          <div className="p-6">
            {/* Profile Info */}
            {showProfile && profile && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-8"
              >
                <h3 className="text-gray-800 font-semibold mb-4 flex items-center">
                  <Sparkles className="w-4 h-4 mr-2 text-purple-500" />
                  About Assaf
                </h3>
                <div className="space-y-3">
                  <motion.div 
                    whileHover={{ scale: 1.02 }}
                    className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-100"
                  >
                    <p className="text-gray-600 text-sm mb-1">Languages</p>
                    <p className="text-gray-800 font-medium">{profile.languages?.join(', ') || 'Loading...'}</p>
                  </motion.div>
                  <motion.div 
                    whileHover={{ scale: 1.02 }}
                    className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-100"
                  >
                    <p className="text-gray-600 text-sm mb-1">Relationships</p>
                    <p className="text-gray-800 font-medium">{profile.relationships?.length || 0} known</p>
                  </motion.div>
                  <motion.div 
                    whileHover={{ scale: 1.02 }}
                    className="p-4 bg-gradient-to-r from-pink-50 to-orange-50 rounded-xl border border-pink-100"
                  >
                    <p className="text-gray-600 text-sm mb-1">Life Events</p>
                    <p className="text-gray-800 font-medium">{profile.important_events?.length || 0} recorded</p>
                  </motion.div>
                </div>
              </motion.div>
            )}
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col bg-gradient-to-b from-gray-50 to-gray-100">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.length === 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-center py-16"
                >
                  <motion.div
                    animate={{ y: [0, -10, 0] }}
                    transition={{ duration: 3, repeat: Infinity }}
                    className="relative inline-block"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full blur-2xl opacity-20"></div>
                    <div className="relative bg-gradient-to-r from-purple-500 to-pink-500 p-6 rounded-full shadow-lg">
                      <MessageCircle className="w-16 h-16 text-white" />
                    </div>
                  </motion.div>
                  <motion.h2 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mt-6"
                  >
                    Welcome to Assaf's World
                  </motion.h2>
                  <motion.p 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="text-gray-600 mt-3 text-lg"
                  >
                    Im Assafs personal agent - ask me anything about him!
                  </motion.p>
                </motion.div>
              )}

              <AnimatePresence>
                {messages.map((message, index) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ delay: index * 0.1 }}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-2xl ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                      <div className={`flex items-start space-x-3 ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                        <motion.div
                          whileHover={{ scale: 1.1 }}
                          className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-md ${
                            message.role === 'user' 
                              ? 'bg-gradient-to-r from-blue-500 to-purple-500' 
                              : 'bg-gradient-to-r from-purple-500 to-pink-500'
                          }`}
                        >
                          {message.role === 'user' ? (
                            <User className="w-5 h-5 text-white" />
                          ) : (
                            <Bot className="w-5 h-5 text-white" />
                          )}
                        </motion.div>
                        <motion.div
                          whileHover={{ scale: 1.02 }}
                          className={`px-5 py-4 rounded-2xl shadow-sm ${
                            message.role === 'user'
                              ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                              : 'bg-white border border-gray-200 text-gray-800'
                          }`}
                        >
                          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                          {message.sources && message.sources.length > 0 && (
                            <div className={`mt-3 text-xs ${
                              message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                            }`}>
                              📚 Sources: {message.sources.length} files
                            </div>
                          )}
                        </motion.div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="flex items-start space-x-3">
                    <div className="shrink-0 w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center shadow-md">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="px-5 py-4 rounded-2xl bg-white border border-gray-200 shadow-sm">
                      <div className="flex space-x-1">
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 0.6, repeat: Infinity }}
                          className="w-2 h-2 bg-purple-400 rounded-full"
                        ></motion.div>
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                          className="w-2 h-2 bg-purple-400 rounded-full"
                        ></motion.div>
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                          className="w-2 h-2 bg-purple-400 rounded-full"
                        ></motion.div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200/80 p-6 bg-white/90 backdrop-blur-xl">
            <div className="max-w-4xl mx-auto">
              <motion.div 
                className={`relative bg-white rounded-2xl border-2 shadow-sm transition-all duration-300 ${
                  isTyping 
                    ? 'border-purple-400 shadow-purple-100' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                whileFocus={{ scale: 1.01 }}
              >
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleInputChange}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about Assaf (English or Hebrew)..."
                  className="w-full px-6 py-4 bg-transparent text-gray-800 placeholder-gray-400 resize-none focus:outline-none rounded-2xl"
                  rows={1}
                  style={{ minHeight: '60px', maxHeight: '120px' }}
                />
                
                {isTyping && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute right-20 top-1/2 transform -translate-y-1/2"
                  >
                    <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
                  </motion.div>
                )}
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isLoading}
                  className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-3 rounded-xl transition-all ${
                    input.trim() && !isLoading
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md hover:shadow-lg'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  <Send className="w-5 h-5" />
                </motion.button>
              </motion.div>
              
              <div className="flex items-center justify-between mt-4">
                <motion.p 
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 3, repeat: Infinity }}
                  className="text-sm text-gray-600"
                >
                  ✨ I&apos;m Assaf&apos;s personal agent - ask me anything about him! (English or Hebrew)
                </motion.p>
                <div className="flex items-center space-x-2">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="p-2 text-gray-400 hover:text-purple-500 transition-colors"
                    title="Voice input (coming soon)"
                  >
                    <Mic className="w-4 h-4" />
                  </motion.button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
