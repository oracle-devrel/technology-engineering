"use client";

import { useEffect, useState, useRef } from "react";

const TypingEffect = ({ text, speed = 30, delay = 0, children }) => {
  const [displayedText, setDisplayedText] = useState("");
  const currentIndexRef = useRef(0);
  
  useEffect(() => {
    if (!text) {
      setDisplayedText("");
      currentIndexRef.current = 0;
      return;
    }
    
    // If text has been shortened (shouldn't happen), reset
    if (text.length < currentIndexRef.current) {
      currentIndexRef.current = 0;
      setDisplayedText("");
    }
    
    const startTyping = () => {
      const interval = setInterval(() => {
        if (currentIndexRef.current < text.length) {
          setDisplayedText(text.substring(0, currentIndexRef.current + 1));
          currentIndexRef.current++;
        } else {
          clearInterval(interval);
        }
      }, speed);
      
      return interval;
    };
    
    const timeout = setTimeout(startTyping, delay);
    
    return () => {
      clearTimeout(timeout);
    };
  }, [text, speed, delay]);
  
  // If children is a function, call it with displayedText
  if (typeof children === 'function') {
    return children(displayedText);
  }
  
  // Otherwise just return the text
  return <>{displayedText}</>;
};

export default TypingEffect;