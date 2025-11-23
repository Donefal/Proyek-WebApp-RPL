import { useParams } from "react-router-dom";

export default function Ticket() {
  const { id } = useParams();
  return (
    <div style={{ padding: 20 }}>
      <h1>Ticket ID: {id}</h1>
    </div>
  );
}
