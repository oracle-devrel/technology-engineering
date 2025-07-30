import { AutoAwesome } from "@mui/icons-material";
import { Box, Chip, Stack, Typography } from "@mui/material";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import DocumentPeekStack from "./DocumentFanStack";

export default function AnalysisResult({
  input,
  submissionData,
  isError,
  isLoading,
}) {
  if (!input && !isLoading) return null;

  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        gap: 2,
        pb: 6,
        pt: 2,
        justifyContent: "center",
      }}
    >
      {!isError && (
        <>
          <motion.div
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{
              duration: 0.6,
              delay: 0.2,
              ease: "easeOut",
            }}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              flexShrink: 0,
            }}
          >
            <DocumentPeekStack documents={submissionData?.files || []} />

            {/* Submission Context debajo del DocumentPeekStack */}
            {submissionData && (
              <Box
                sx={{
                  p: 2,
                  backgroundColor: "rgba(255, 255, 255, 0.02)",
                  borderRadius: 2,
                  width: "100%",
                  maxWidth: 300,
                }}
              >
                <Stack spacing={2}>
                  {/* Files */}
                  {submissionData.files?.length > 0 && (
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{ mb: 1, color: "text.secondary" }}
                      >
                        Documents Evaluated:
                      </Typography>
                      <Box
                        sx={{
                          display: "grid",
                          gridTemplateColumns:
                            "repeat(auto-fit, minmax(100px, 1fr))",
                          gap: 1,
                        }}
                      >
                        {submissionData.files.map((fileName, index) => (
                          <Chip
                            key={index}
                            label={fileName}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {/* Criteria */}
                  {submissionData.criteria && (
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{ mb: 1, color: "text.secondary" }}
                      >
                        Criteria Used:
                      </Typography>
                      {submissionData.criteria.type === "csv" ? (
                        <Chip
                          label={`CSV: ${submissionData.criteria.name}`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      ) : (
                        <Box
                          sx={{
                            display: "grid",
                            gridTemplateColumns:
                              "repeat(auto-fit, minmax(120px, 1fr))",
                            gap: 1,
                          }}
                        >
                          {Object.entries(submissionData.criteria.criteria).map(
                            ([key, value], index) => (
                              <Chip
                                key={index}
                                label={`${key}: ${value}`}
                                size="small"
                                color="primary"
                                variant="outlined"
                              />
                            )
                          )}
                        </Box>
                      )}
                    </Box>
                  )}

                  {/* Instructions */}
                  {submissionData.instructions && (
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{ mb: 1, color: "text.secondary" }}
                      >
                        Additional Instructions:
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          color: "text.primary",
                          fontStyle: "italic",
                          backgroundColor: "rgba(255, 255, 255, 0.05)",
                          borderRadius: 1,
                          py: 0.25,
                        }}
                      >
                        "{submissionData.instructions}"
                      </Typography>
                    </Box>
                  )}
                </Stack>
              </Box>
            )}
          </motion.div>

          {/* Separador vertical animado */}
          <motion.div
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{
              duration: 0.8,
              delay: 0.5,
              ease: "easeOut",
            }}
            style={{
              originY: 0.5,
              alignSelf: "stretch",
              margin: "0 24px",
            }}
          >
            <Box
              sx={{
                width: "1px",
                height: "100%",
                background: (theme) =>
                  `linear-gradient(to bottom, transparent 0%, ${theme.palette.divider} 20%, ${theme.palette.divider} 80%, transparent 100%)`,
              }}
            />
          </motion.div>

          {/* Evaluation Result - solo en la columna derecha */}
          <Box sx={{ mt: "20px", flex: 1, maxWidth: "100%", overflow: "auto" }}>
            {input && (
              <motion.div
                initial={{ x: 100, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{
                  duration: 0.6,
                  ease: "easeOut",
                }}
              >
                <Box
                  sx={{
                    p: 2,
                    backgroundColor: "rgba(255, 255, 255, 0.02)",
                    borderRadius: 2,
                  }}
                >
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{ mb: 2 }}
                  >
                    <AutoAwesome
                      sx={{ color: "text.secondary", fontSize: 20 }}
                    />
                    <Typography variant="h6" sx={{ color: "text.secondary" }}>
                      Evaluation Result
                    </Typography>
                  </Stack>
                  <Box
                    sx={{
                      color: "text.primary",
                      lineHeight: 1.6,
                      "& p": { mb: 1 },
                      "& h1, & h2, & h3": { color: "text.secondary", mb: 1 },
                      "& ul, & ol": { pl: 2, mb: 1 },
                      "& code": {
                        backgroundColor: "rgba(255, 255, 255, 0.1)",
                        padding: "2px 4px",
                        borderRadius: 1,
                        fontSize: "0.9em",
                      },
                      "& table": {
                        width: "100%",
                        borderCollapse: "collapse",
                        mb: 2,
                        minWidth: "500px",
                      },
                      "& .table-container": {
                        overflowX: "auto",
                        mb: 2,
                      },
                      "& th, & td": {
                        border: (theme) => `1px solid ${theme.palette.divider}`,
                        padding: "8px 12px",
                        textAlign: "left",
                      },
                      "& th": {
                        backgroundColor: (theme) => theme.palette.action.hover,
                        fontWeight: "bold",
                      },
                    }}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        table: ({ children, ...props }) => (
                          <div className="table-container">
                            <table {...props}>{children}</table>
                          </div>
                        ),
                      }}
                    >
                      {input}
                    </ReactMarkdown>
                  </Box>
                </Box>
              </motion.div>
            )}
          </Box>
        </>
      )}
    </Box>
  );
}
