import React, { useState, useEffect } from 'react';

interface InsightsProps {
  recommendationId: number;
}

const Insights: React.FC<InsightsProps> = ({ recommendationId }) => {
  const [insights, setInsights] = useState([]);

  useEffect(() => {
    fetch(`/api/recommendations/${recommendationId}/insights`)
      .then((res) => res.json())
      .then((data) => setInsights(data));
  }, [recommendationId]);

  return (
    <div>
      <h3>Additional Insights from RAG Agent</h3>
      <ul>
        {insights.map((insight: any, index: number) => (
          <li key={index}>{insight}</li>
        ))}
      </ul>
    </div>
  );
};

export default Insights;
