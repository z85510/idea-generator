import concurrently from 'concurrently';

concurrently([
   {
      name: 'server',
      command: './run.sh',
      prefixColor: 'cyan',
      cwd: 'packages/server',
   },
   {
      name: 'client',
      command: 'bun run dev',
      prefixColor: 'magenta',
      cwd: 'packages/client',
   },
]);
