"use client";

import { createContext, useContext, useReducer } from "react";

const ValidationContext = createContext();

const initialState = {
  status: "idle",
  quality: {
    status: "pending",
    issues: [],
    recommendations: [],
    qualityScore: null,
  },
  overallResult: "pending",
};

function validationReducer(state, action) {
  switch (action.type) {
    case "VALIDATION_STARTED":
      return {
        ...initialState,
        status: "in_progress",
      };
    case "VALIDATION_COMPLETE":
      return {
        ...state,
        status: "complete",
        overallResult: action.payload.overallResult,
      };
    case "VALIDATION_ERROR":
      return {
        ...state,
        status: "error",
        error: action.payload.error,
      };
    case "QUALITY_VALIDATED":
      return {
        ...state,
        quality: {
          status: "complete",
          issues: action.payload.issues,
          recommendations: action.payload.recommendations,
          qualityScore: action.payload.qualityScore,
        },
      };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

export function ValidationProvider({ children }) {
  const [state, dispatch] = useReducer(validationReducer, initialState);

  const value = {
    state,
    startValidation: () => {
      dispatch({ type: "VALIDATION_STARTED" });
    },
    completeValidation: (overallResult) => {
      dispatch({
        type: "VALIDATION_COMPLETE",
        payload: { overallResult },
      });
    },
    setValidationError: (error) => {
      dispatch({ type: "VALIDATION_ERROR", payload: { error } });
    },
    setQualityResult: (issues, recommendations, qualityScore) => {
      dispatch({
        type: "QUALITY_VALIDATED",
        payload: { issues, recommendations, qualityScore },
      });
    },
    resetValidation: () => {
      dispatch({ type: "RESET" });
    },
  };

  return (
    <ValidationContext.Provider value={value}>
      {children}
    </ValidationContext.Provider>
  );
}

export function useValidation() {
  const context = useContext(ValidationContext);
  if (context === undefined) {
    throw new Error("useValidation must be used within a ValidationProvider");
  }
  return context;
}
