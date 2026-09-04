"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Home from "../../page";

export default function ConversationPage() {
  const params = useParams();
  const [conversationId, setConversationId] = useState(null);

  useEffect(() => {
    if (params?.id) {
      setConversationId(params.id);
    }
  }, [params?.id]);

  // Pass the conversation ID to the Home component
  return <Home initialConversationId={conversationId} />;
}
