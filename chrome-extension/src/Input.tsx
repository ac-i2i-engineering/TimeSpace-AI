import { TextField, InputAdornment, IconButton } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import { useState } from "react";

interface InputProps {
   onSend: (message: string) => void;
}

const Input = ({ onSend }: InputProps) => {
   const [inputValue, setInputValue] = useState<string>("");

   const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      setInputValue(event.target.value);
   };

   return (
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
         onChange={handleInputChange}
         slotProps={{
            input: {
               endAdornment: (
                  <InputAdornment position="end">
                     <IconButton onClick={() => onSend(inputValue)}>
                        <SendIcon />
                     </IconButton>
                  </InputAdornment>
               ),
            },
         }}
      />
   );
};

export default Input;
