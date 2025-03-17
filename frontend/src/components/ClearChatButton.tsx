import { Button } from '@chakra-ui/react';
import { DeleteIcon } from '@chakra-ui/icons';

interface ClearChatButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

export const ClearChatButton: React.FC<ClearChatButtonProps> = ({ disabled, onClick }) => {
  return (
    <Button
      leftIcon={<DeleteIcon />}
      colorScheme="red"
      variant="outline"
      onClick={onClick}
      disabled={disabled}
    >
      Clear Chat
    </Button>
  );
};
