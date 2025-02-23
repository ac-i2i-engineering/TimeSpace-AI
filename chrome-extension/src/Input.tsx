import { TextField, InputAdornment, IconButton } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";

const Input = () => (
   <TextField
      variant="standard"
      label="Chat with Indigo"
      style={{
         position: "fixed",
         bottom: "4rem",
         left: "5%",
         width: "90%",
      }}
      multiline
      color="secondary"
      slotProps={{
         input: {
            endAdornment: (
               <InputAdornment position="end">
                  <IconButton onClick={() => window.location.reload()}>
                     <SendIcon />
                  </IconButton>
               </InputAdornment>
            ),
         },
      }}
   />
);

export default Input;
