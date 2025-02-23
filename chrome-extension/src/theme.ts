import { createTheme, ThemeProvider } from "@mui/material/styles";

const theme = createTheme({
   palette: {
      mode: "dark",
      primary: {
         main: "rgb(251, 240, 232)",
         light: "rgb(230, 224, 204)",
         dark: "rgb(230, 224, 204)",
      },
      secondary: {
         main: "rgb(230, 224, 204)",
      },
   },
   typography: {
      fontFamily: "Lato, sans-serif",
      h1: {
         fontSize: "2rem",
      },
   },
   components: {
      MuiTextField: {
         styleOverrides: {
            root: {
               textTransform: "none",
            },
         },
      },
   },
});

export { theme, ThemeProvider };
