export const getComponentOverrides = (theme) => ({
  MuiButton: {
    styleOverrides: {
      root: {
        textTransform: "none",
        borderRadius: theme.shape.borderRadius * 2,
        boxShadow: "none",
        "&:hover": {
          boxShadow: "none",
        },
      },
    },
  },
  MuiAvatar: {
    styleOverrides: {
      root: {
        fontSize: "0.875rem",
        fontWeight: 600,
      },
    },
  },
  MuiListItemButton: {
    styleOverrides: {
      root: {
        borderRadius: "4px",
        margin: "2px 0",
        "&:hover": {
          backgroundColor: "rgba(255,255,255,0.1)",
        },
      },
    },
  },
  MuiListItemIcon: {
    styleOverrides: {
      root: {
        minWidth: "36px",
      },
    },
  },
  MuiDivider: {
    styleOverrides: {
      root: {
        borderColor: "rgba(255,255,255,0.1)",
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        backgroundColor: theme.palette.background.paper,
        boxShadow: "none",
        border: "1px solid rgba(255,255,255,0.1)",
      },
    },
  },
});
