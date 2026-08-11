const history = { english: [], spanish: [] };
const maxLines = 5;

function render(kind) {
  const target = document.querySelector(`#${kind} .history`);
  target.replaceChildren(...history[kind].map((text) => {
    const item = document.createElement("p");
    item.textContent = text;
    return item;
  }));
}

const stream = new EventSource("/events");
stream.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.kind === "status") {
    document.querySelector("#status").textContent = message.text;
  }
  if (message.kind === "english" || message.kind === "spanish") {
    history[message.kind].push(message.text);
    history[message.kind] = history[message.kind].slice(-maxLines);
    render(message.kind);
  }
};
stream.onerror = () => {
  document.querySelector("#status").textContent = "Reconnecting to local demo…";
};
