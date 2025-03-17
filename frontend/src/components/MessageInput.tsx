import { Flex, Input, Button } from '@chakra-ui/react';

interface MessageInputProps {
  value: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSend: () => void;
}

const MessageInput: React.FC<MessageInputProps> = ({ value, onChange, onSend }) => (
  <Flex w="100%">
    <Input
      flex="1"
      placeholder="Type your message..."
      value={value}
      onChange={onChange}
      onKeyDown={(e) => e.key === 'Enter' && onSend()}  // Send on Enter
    />
    <Button colorScheme="blue" onClick={onSend} ml={2}>Send</Button>
  </Flex>
);

export default MessageInput;
