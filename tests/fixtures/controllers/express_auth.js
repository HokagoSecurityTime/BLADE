app.get('/users/:userId', (req, res) => {
  if (req.user.roles.includes('admin')) return res.json(db.user(req.params.userId));
  if (req.user.id === req.params.userId) return res.json(db.user(req.params.userId));
  return res.status(403).end();
});
app.get('/orgs/:orgId/docs', (req, res) => {
  if (req.user.tenant_id === req.params.orgId) return res.json(db.docs(req.params.orgId));
  return res.sendStatus(403);
});
