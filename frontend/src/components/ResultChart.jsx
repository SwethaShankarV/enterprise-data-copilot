import React from "react";
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function ResultChart({data}){
  // expect data = { labels: [...], values: [...] }
  const chartData = {
    labels: data.labels,
    datasets: [{ label: data.label || 'Value', data: data.values }]
  };
  return <div className="my-4"><Bar data={chartData} /></div>;
}