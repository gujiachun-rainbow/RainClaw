import { computed, Ref, unref } from 'vue';
import { Message } from '../types/message';

export interface GroupedMessage {
  type: 'single' | 'process';
  message?: Message;
  messages?: Message[];
  id: string;
}

export function useMessageGrouper(messagesRef: Ref<Message[]> | Message[]) {
  const groupedMessages = computed<GroupedMessage[]>(() => {
    const messages = unref(messagesRef);
    const groups: GroupedMessage[] = [];
    let currentProcessGroup: Message[] = [];
    let currentAssistantGroup: Message[] = [];

    let processGroupCounter = 0;
    let assistantGroupCounter = 0;

    const flushProcessGroup = () => {
      if (currentProcessGroup.length > 0) {
        const firstIdx = messages.indexOf(currentProcessGroup[0]);
        groups.push({
          type: 'process',
          messages: [...currentProcessGroup],
          id: `process-${firstIdx}-${processGroupCounter++}`
        });
        currentProcessGroup = [];
      }
    };

    const flushAssistantGroup = () => {
      if (currentAssistantGroup.length > 0) {
        const firstMsg = currentAssistantGroup[0];
        const firstIdx = messages.indexOf(currentAssistantGroup[0]);
        const mergedContent = currentAssistantGroup
          .map(m => (m.content as any).content || '')
          .join('\n\n');
        
        const mergedMsg: Message = {
          ...firstMsg,
          content: {
            ...firstMsg.content,
            content: mergedContent
          } as any
        };

        groups.push({
          type: 'single',
          message: mergedMsg,
          id: `merged-assistant-${firstIdx}-${assistantGroupCounter++}`
        });
        currentAssistantGroup = [];
      }
    };

    messages.forEach((msg, index) => {
      if (msg.type === 'step' || msg.type === 'tool') {
        flushAssistantGroup();
        currentProcessGroup.push(msg);
      } else if (msg.type === 'assistant') {
        flushProcessGroup();
        currentAssistantGroup.push(msg);
      } else {
        flushProcessGroup();
        flushAssistantGroup();
        groups.push({
          type: 'single',
          message: msg,
          id: `msg-${index}`
        });
      }
    });

    flushProcessGroup();
    flushAssistantGroup();
    return groups;
  });

  return {
    groupedMessages
  };
}
