import { Brain, Database, Shield, AlertTriangle, ListTodo, Wrench, ScanEye, Lightbulb, SatelliteDish, FileSpreadsheet, Mail } from "lucide-react";

// Icon mapping
const iconMap = {
  "Brain": Brain,
  "Database": Database,
  "Shield": Shield,
  "AlertTriangle": AlertTriangle,
  "ListTodo": ListTodo,
  "Wrench": Wrench,
  "ScanEye": ScanEye,
  "Lightbulb": Lightbulb,
  "SatelliteDish": SatelliteDish,
  "FileSpreadsheet": FileSpreadsheet,
  "Mail": Mail
};

// Import all mock files
// import databaseErrors from '../mocks/database-errors.json';
import defaultMock from '../mocks/default.json';
// import orderPartsInitial from '../mocks/order-parts-initial.json';
// import orderPartsHeavyDuty from '../mocks/order-parts-heavy-duty.json';
// import orderPartsStandard from '../mocks/order-parts-standard.json';
import partsSearchFlow from '../mocks/parts-search-flow.json';
import partsAutonomyFlow from '../mocks/parts-autonomy-flow.json';
import partsAdvisoryFlow from '../mocks/parts-advisory-flow.json';
import partSelectionHd2024 from '../mocks/part-selection-hd2024.json';
import supplierContactFlow from '../mocks/supplier-contact-flow.json';
import offerAnalysisFlow from '../mocks/offer-analysis-flow.json';
import orderCreationFlow from '../mocks/order-creation-flow.json';
import orderStatusFlow from '../mocks/order-status-flow.json';
import thankYou from '../mocks/thank-you.json';

const mockFlows = [
  // databaseErrors,
  thankYou,
  partsSearchFlow,
  partsAutonomyFlow,
  partsAdvisoryFlow,
  partSelectionHd2024,
  supplierContactFlow,
  offerAnalysisFlow,
  orderCreationFlow,
  orderStatusFlow,
  // orderPartsInitial,
  // orderPartsHeavyDuty, 
  // orderPartsStandard,
  defaultMock
];

// Context state for tracking interactive flows
let conversationContext = {
  waitingForChoice: false,
  lastFlowId: null,
  awaitingFollowUp: false,
  followUpFlowId: null
};

/**
 * Finds the best matching mock flow based on user input
 * @param {string} userInput - The user's input message
 * @param {Object} previousState - Optional previous conversation state
 * @returns {Object} The selected mock flow with processed icons
 */
export function getMockFlow(userInput, previousState = null) {
  const input = userInput.toLowerCase();
  
  // Update context if provided
  if (previousState) {
    conversationContext = { ...conversationContext, ...previousState };
  }
  
  // Get all flows including custom ones from localStorage
  const allFlows = getAllMockFlows();
  
  // Check if we're awaiting a follow-up response
  if (conversationContext.awaitingFollowUp && conversationContext.followUpFlowId) {
    // Find the flow that was waiting for follow-up
    const previousFlow = allFlows.find(f => f.id === conversationContext.followUpFlowId);
    
    if (previousFlow && previousFlow.followUpTriggerPhrases && previousFlow.followUpMessages) {
      // Check if user input matches any follow-up trigger phrases exactly
      const hasFollowUpMatch = previousFlow.followUpTriggerPhrases.some(phrase => 
        input === phrase.toLowerCase()
      );
      
      if (hasFollowUpMatch) {
        // Process follow-up messages
        const processedMessages = previousFlow.followUpMessages.map(message => {
          if (message.type === "chip" && message.chipData.icon) {
            return {
              ...message,
              chipData: {
                ...message.chipData,
                icon: iconMap[message.chipData.icon] || Brain
              }
            };
          }
          return message;
        });
        
        // Reset follow-up context
        conversationContext.awaitingFollowUp = false;
        conversationContext.followUpFlowId = null;
        
        // Check if follow-up has interactive elements
        const hasInteractiveMessage = previousFlow.followUpMessages.some(msg => msg.type === "interactive");
        if (hasInteractiveMessage) {
          conversationContext.waitingForChoice = true;
          conversationContext.lastFlowId = previousFlow.id;
        }
        
        return {
          ...previousFlow,
          messages: processedMessages,
          context: conversationContext
        };
      }
    }
  }
  
  // Find the best matching flow using exact phrase matching
  let bestMatch = defaultMock;
  
  for (const flow of allFlows) {
    // Skip disabled flows
    if (flow.isDisabled) continue;
    
    if (!flow.triggerPhrases || flow.triggerPhrases.length === 0) continue; // Skip flows without trigger phrases
    
    // Check if user input matches any trigger phrase exactly
    const hasExactMatch = flow.triggerPhrases.some(phrase => 
      input === phrase.toLowerCase()
    );
    
    if (hasExactMatch) {
      bestMatch = flow;
      break; // Use first exact match found
    }
  }
  
  // Update context based on selected flow
  const hasInteractiveMessage = bestMatch.messages.some(msg => msg.type === "interactive");
  const hasFollowUpMessages = bestMatch.followUpTriggerPhrases && bestMatch.followUpMessages;
  
  if (hasInteractiveMessage) {
    conversationContext.waitingForChoice = true;
    conversationContext.lastFlowId = bestMatch.id;
  } else if (hasFollowUpMessages) {
    // Set up follow-up context
    conversationContext.awaitingFollowUp = true;
    conversationContext.followUpFlowId = bestMatch.id;
    conversationContext.waitingForChoice = false;
  } else {
    conversationContext.waitingForChoice = false;
    conversationContext.awaitingFollowUp = false;
  }
  
  // Process the selected flow to replace icon strings with actual components
  const processedMessages = bestMatch.messages.map(message => {
    if (message.type === "chip" && message.chipData.icon) {
      return {
        ...message,
        chipData: {
          ...message.chipData,
          icon: iconMap[message.chipData.icon] || Brain
        }
      };
    }
    return message;
  });
  
  return {
    ...bestMatch,
    messages: processedMessages,
    context: conversationContext
  };
}

/**
 * Gets all available mock flows (for debugging/admin purposes)
 * @returns {Array} Array of all mock flows
 */
export function getAllMockFlows() {
  // Load custom flows from localStorage
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('customAgentFlows');
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch (e) {
        console.error('Error parsing stored flows:', e);
      }
    }
  }
  return mockFlows;
}