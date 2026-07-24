export const getErrorMessage = (error) => {
  const defaultMessage =
    "Lo siento, hubo un problema al conectar con el agente.";

  if (!error?.message) {
    return defaultMessage;
  }

  // Map specific error patterns to user-friendly messages
  const errorPatterns = [
    {
      pattern: /API Error: 500|500 -|Internal Server Error/i,
      message:
        "Error interno del servidor. Por favor, contacta con el administrador del sistema.",
    },
    {
      pattern: /API Error: 503|503 -|Service Unavailable/i,
      message:
        "El servicio no está disponible temporalmente. Por favor, intenta de nuevo en unos minutos.",
    },
    {
      pattern: /API Error: 401|401 -|Unauthorized/i,
      message:
        "Error de autenticación. Por favor, contacta con el administrador del sistema.",
    },
    {
      pattern: /API Error: 403|403 -|Forbidden/i,
      message:
        "No tienes permisos para realizar esta acción. Contacta con el administrador.",
    },
    {
      pattern: /API Error: 429|429 -|Too Many Requests/i,
      message:
        "Demasiadas solicitudes. Por favor, espera un momento antes de intentar de nuevo.",
    },
    {
      pattern: /Tool.*disabled|mcp.*disabled|'mcp'.*disabled/i,
      message:
        "Las herramientas MCP no están habilitadas para esta organización. Contacta con el administrador de OCI para habilitar esta función.",
    },
    {
      pattern: /API Error: 400.*invalid_request_error/i,
      message:
        "Error en la configuración de la solicitud. Revisa los parámetros enviados.",
    },
    {
      pattern: /API Error: 4\d{2}/i,
      message:
        "Error en la solicitud. Por favor, intenta de nuevo.",
    },
    {
      pattern: /Read timed out|timed out/i,
      message:
        "La conexión tardó demasiado tiempo. Por favor, intenta de nuevo.",
    },
    {
      pattern: /SSE processing failed/i,
      message:
        "Hubo un problema al procesar la respuesta. Por favor, intenta de nuevo.",
    },
    {
      pattern: /Connection reset|Connection aborted/i,
      message:
        "Se perdió la conexión con el servidor. Por favor, intenta de nuevo.",
    },
    {
      pattern: /Network error|Failed to fetch|fetch failed/i,
      message: "Error de red. Por favor, verifica tu conexión a internet.",
    },
    {
      pattern: /OCI_GENAI_PROJECT_ID is required|OCI_COMPARTMENT_ID is required/i,
      message:
        "Configuración incompleta. Por favor, contacta con el administrador del sistema.",
    },
  ];

  // Find matching pattern
  const match = errorPatterns.find(({ pattern }) =>
    pattern.test(error.message)
  );

  if (match) {
    return match.message;
  }

  // For any other API errors, show a generic message
  if (/API Error/i.test(error.message)) {
    return "Error al comunicarse con el servidor. Por favor, contacta con el administrador del sistema.";
  }

  // Return a user-friendly version of the error
  return defaultMessage;
};
