"use client";

import { createContext, useContext, useState, useCallback } from "react";

const WidgetV2FormContext = createContext({
  state: {},
  update: () => {},
  disabled: false,
  onSubmit: null,
  __hasProvider: false,
});

export function WidgetV2FormProvider({ children, onSubmit, disabled = false }) {
  const [state, setState] = useState({});

  const update = useCallback((key, value) => {
    setState(prev => ({ ...prev, [key]: value }));
  }, []);

  const getFormData = useCallback(() => state, [state]);

  return (
    <WidgetV2FormContext.Provider value={{ state, update, disabled, onSubmit, getFormData, __hasProvider: true }}>
      {children}
    </WidgetV2FormContext.Provider>
  );
}

export function useV2Form() {
  return useContext(WidgetV2FormContext);
}

export default WidgetV2FormContext;
