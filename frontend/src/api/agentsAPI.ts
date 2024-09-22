// export async function fetchRecommendations() {
//     const response = await fetch('/api/recommendations');
//     return await response.json();
//   }

export async function fetchAgentsConversation() {
  const response = await fetch('/api/start-agents', { method: 'POST' });
  return await response.json();
}
