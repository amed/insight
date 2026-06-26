// bi fields and the query used to retrieve the lines that support each.
// the same grounded extraction loop is run for every entry (see processingService).
module.exports = [
  { name: 'intent', query: 'what does the customer want?' },
  { name: 'issue_type', query: 'what kind of problem or issue is described?' },
  { name: 'sentiment', query: 'how does the customer feel, positive, negative, or neutral?' },
  { name: 'resolution_status', query: 'was the issue resolved?' },
  { name: 'risk', query: 'is there a risk of churn, escalation, or complaint?' },
  { name: 'next_action', query: 'what is the next action or follow-up?' },
];
