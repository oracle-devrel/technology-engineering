import { motion } from "framer-motion";
import { useState } from "react";

const MOCK_CONTENT = `Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam
          vehicula risus non lorem elementum, sed placerat orci suscipit.
          Vestibulum ante ipsum primis in faucibus orci luctus et ultrices
          posuere cubilia curae; Vivamus sit amet semper urna. Sed euismod,
          ipsum at facilisis pulvinar, mauris urna hendrerit arcu, id
          sollicitudin dolor lectus vitae ligula. Duis auctor nisi vel ex
          tincidunt, vitae scelerisque erat tincidunt.`;

function DocumentCard({
  content,
  type = "Mock",
  index,
  totalCards,
  hoveredIndex,
  onHover,
  onLeave,
}) {
  const springConfig = { type: "spring", stiffness: 300, damping: 30 };

  const baseOffset = index * 15;
  const expandedOffset = index * 25;
  const baseRotation = (index - (totalCards - 1) / 2) * 8;
  const expandedRotation = (index - (totalCards - 1) / 2) * 15;

  const translateX = hoveredIndex !== null ? expandedOffset : baseOffset;
  const translateY = hoveredIndex === index && index > 0 ? -40 : 0;
  const scale = hoveredIndex === index ? 1.05 : 1;
  const zIndex = totalCards - index;
  const rotate = hoveredIndex !== null ? expandedRotation : baseRotation;

  // Separar título de las líneas de guiones
  const isFileName = content && !content.includes("\n");
  const title = isFileName ? content : content?.split("\n")[0] || "";
  const dashLines = Array(12).fill("━━━━━━━━━━━━━━━━━━━━━━━━").join("\n");

  return (
    <motion.div
      animate={{
        x: translateX,
        y: translateY,
        scale: scale,
        rotate: rotate,
        zIndex: zIndex,
      }}
      transition={springConfig}
      onHoverStart={() => onHover(index)}
      onHoverEnd={onLeave}
      style={{
        width: "140px",
        height: "190px",
        background: "#ffffff",
        borderRadius: 8,
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        padding: "16px",
        paddingBottom: "8px",
        overflow: "hidden",
        cursor: "pointer",
        position: "absolute",
        left: 0,
        top: 0,
      }}
    >
      {/* Título con truncamiento de una línea */}
      <div
        style={{
          margin: 0,
          fontFamily: "Georgia, serif",
          fontSize: "11px",
          lineHeight: "1.3",
          color: "#424242",
          overflow: "hidden",
          whiteSpace: "nowrap",
          textOverflow: "ellipsis",
          marginBottom: "8px",
        }}
      >
        {title}
      </div>

      {/* Líneas de guiones */}
      <div
        style={{
          margin: 0,
          fontFamily: "Georgia, serif",
          fontSize: "11px",
          lineHeight: "1.3",
          color: "rgba(66, 66, 66, 0.4)",
          overflow: "hidden",
          display: "-webkit-box",
          WebkitLineClamp: 10,
          WebkitBoxOrient: "vertical",
        }}
      >
        {dashLines}
      </div>
    </motion.div>
  );
}

export default function DocumentPeekStack({ documents = [] }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  const defaultDocuments = [
    { content: MOCK_CONTENT },
    { content: MOCK_CONTENT },
    { content: MOCK_CONTENT },
    { content: MOCK_CONTENT },
  ];

  // Si documents es un array de strings (nombres de archivos), convertirlos a objetos
  const processedDocuments = documents.map((doc) => {
    if (typeof doc === "string") {
      return {
        content: doc,
        type: "Document",
      };
    }
    return doc;
  });

  const docsToRender =
    processedDocuments.length > 0 ? processedDocuments : defaultDocuments;

  // Calcular ancho necesario basado en número de documentos
  const containerWidth = Math.max(200, docsToRender.length * 20 + 140);

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "250px",
        position: "relative",
        width: "fit-content",
      }}
    >
      <div
        style={{
          position: "relative",
          width: `${containerWidth}px`,
          height: "190px",
        }}
      >
        {docsToRender.map((doc, index) => (
          <DocumentCard
            key={index}
            content={doc.content}
            type={doc.type}
            index={index}
            totalCards={docsToRender.length}
            hoveredIndex={hoveredIndex}
            onHover={setHoveredIndex}
            onLeave={() => setHoveredIndex(null)}
          />
        ))}
      </div>
    </div>
  );
}
