'use client';

import { useState, useEffect, useRef } from 'react';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Input from '@cloudscape-design/components/input';
import Button from '@cloudscape-design/components/button';
import Select from '@cloudscape-design/components/select';
import Box from '@cloudscape-design/components/box';
import Textarea from '@cloudscape-design/components/textarea';
import { FormField, Header, KeyValuePairs } from '@cloudscape-design/components';

const LOG_LEVELS = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR'] as const;
type LogLevel = (typeof LOG_LEVELS)[number];
const LOG_PRIORITY: Record<LogLevel, number> = {
  TRACE: 0,
  DEBUG: 1,
  INFO: 2,
  WARN: 3,
  ERROR: 4,
};

const mockFetchLogs = async (minLevel: LogLevel, contains: string) => {
  // Log data from lorem_logs.txt
  const allLogs = [
    '2025-08-22T10:00:00-05:00 [TRACE] Labore sit consequat aliquip laboris magna ut tempor occaecat amet sit tempor ullamco nisi mollit sit nostrud sint.',
    '2025-08-22T10:00:01-05:00 [DEBUG] Proident consequat lorem enim occaecat voluptate consequat ut ullamco voluptate ut.',
    '2025-08-22T10:00:02-05:00 [INFO] Eu incididunt esse velit ea consectetur sunt laborum et.',
    '2025-08-22T10:00:03-05:00 [WARN] Eiusmod aute cillum quis sed consectetur nisi aute eiusmod nisi incididunt eu consequat sunt.',
    '2025-08-22T10:00:04-05:00 [ERROR] Cillum enim dolore esse exercitation commodo do ad laborum aliquip enim in eu commodo laboris reprehenderit elit nisi.',
    '2025-08-22T10:00:05-05:00 [TRACE] In pariatur commodo sed ullamco in ullamco deserunt.',
    '2025-08-22T10:00:06-05:00 [DEBUG] Sunt aliqua ea magna aliquip laborum ea occaecat pariatur cillum laboris magna anim deserunt.',
    '2025-08-22T10:00:07-05:00 [INFO] Adipiscing labore ut enim occaecat sed fugiat eu in.',
    '2025-08-22T10:00:08-05:00 [WARN] Ex ipsum labore laborum commodo voluptate labore aute cupidatat enim sunt lorem ea mollit minim mollit.',
    '2025-08-22T10:00:09-05:00 [ERROR] Irure mollit nostrud ut dolore enim est lorem reprehenderit.',
    '2025-08-22T10:00:10-05:00 [TRACE] Dolor labore cillum dolor ut elit ut eiusmod eiusmod officia sed laborum dolore dolore culpa.',
    '2025-08-22T10:00:11-05:00 [DEBUG] Ad ea est occaecat ullamco nostrud dolor pariatur dolore non id proident et aliquip laboris sed.',
    '2025-08-22T10:00:12-05:00 [INFO] Dolor nisi laboris lorem do elit nisi sed amet in do anim ut.',
    '2025-08-22T10:00:13-05:00 [WARN] Officia ullamco dolore culpa aliquip culpa excepteur quis incididunt incididunt cupidatat esse.',
    '2025-08-22T10:00:14-05:00 [ERROR] Excepteur in adipiscing incididunt elit pariatur voluptate ut aliquip quis quis laborum proident magna.',
    '2025-08-22T10:00:15-05:00 [TRACE] Veniam consequat in aliquip do non incididunt adipiscing ipsum tempor ut ad excepteur officia.',
    '2025-08-22T10:00:16-05:00 [DEBUG] Ullamco pariatur elit ad eu lorem fugiat ea sunt duis occaecat officia ut quis aute.',
    '2025-08-22T10:00:17-05:00 [INFO] Elit elit in elit adipiscing qui mollit est enim elit anim.',
    '2025-08-22T10:00:18-05:00 [WARN] Veniam sed sed ut pariatur et aliquip consectetur eiusmod.',
    '2025-08-22T10:00:19-05:00 [ERROR] Id in ea exercitation in ut ea nulla dolore irure sunt in do ipsum.',
    '2025-08-22T10:00:20-05:00 [TRACE] Incididunt do laborum ullamco mollit ea dolore velit sed aliquip dolore duis enim non irure.',
    '2025-08-22T10:00:21-05:00 [DEBUG] Est ipsum irure ut magna ea labore ut ut commodo duis exercitation voluptate exercitation ea mollit officia.',
    '2025-08-22T10:00:22-05:00 [INFO] Adipiscing tempor occaecat consequat consectetur lorem in dolore ea enim non occaecat.',
    '2025-08-22T10:00:23-05:00 [WARN] Ipsum labore do ut amet dolore aliqua cupidatat dolore consectetur dolor cillum consectetur esse exercitation aliquip.',
    '2025-08-22T10:00:24-05:00 [ERROR] Ut esse excepteur ut ut enim minim excepteur sit minim in excepteur aliquip commodo enim ut eu amet.',
    '2025-08-22T10:00:25-05:00 [TRACE] Laboris nostrud sunt velit dolor nisi laboris sit quis pariatur in consequat sed consequat velit.',
    '2025-08-22T10:00:26-05:00 [DEBUG] Anim pariatur laborum in sit labore ea minim ea amet ut cupidatat velit in cupidatat anim labore fugiat.',
    '2025-08-22T10:00:27-05:00 [INFO] Quis ex consectetur cupidatat lorem id laborum nostrud cillum cupidatat sed in in et irure mollit dolor.',
    '2025-08-22T10:00:28-05:00 [WARN] Excepteur reprehenderit pariatur aute dolore quis sint eu minim irure pariatur lorem irure duis exercitation cupidatat reprehenderit in.',
    '2025-08-22T10:00:29-05:00 [ERROR] Non ullamco anim culpa ad eiusmod duis anim in tempor ut dolor laboris nostrud aliqua.',
    '2025-08-22T10:00:30-05:00 [TRACE] Consectetur aliquip culpa do sunt sint quis fugiat.',
    '2025-08-22T10:00:31-05:00 [DEBUG] Pariatur aliquip aliqua lorem ut occaecat laboris minim id in adipiscing aliquip et sunt magna.',
    '2025-08-22T10:00:32-05:00 [INFO] Est in non mollit occaecat proident enim culpa proident ea aliquip consequat id officia ut.',
    '2025-08-22T10:00:33-05:00 [WARN] Non do duis ut commodo in in eiusmod magna ut nisi fugiat.',
    '2025-08-22T10:00:34-05:00 [ERROR] Ullamco sed sint excepteur in in sint elit exercitation sint.',
    '2025-08-22T10:00:35-05:00 [TRACE] Dolor eu qui lorem esse irure fugiat sint laborum laboris officia laboris commodo cupidatat.',
    '2025-08-22T10:00:36-05:00 [DEBUG] Sit fugiat voluptate pariatur ad in dolore laborum sit nulla sit eiusmod occaecat magna in.',
    '2025-08-22T10:00:37-05:00 [INFO] Adipiscing ea eu reprehenderit ullamco sunt reprehenderit voluptate eu consequat.',
    '2025-08-22T10:00:38-05:00 [WARN] Ex eiusmod culpa dolor adipiscing velit laboris sed consectetur sit aliquip nostrud dolor ut.',
    '2025-08-22T10:00:39-05:00 [ERROR] Dolore culpa labore ullamco in ex dolore ad labore enim dolor.',
    '2025-08-22T10:00:40-05:00 [TRACE] Sit dolor eu nulla nostrud do aliquip ut irure.',
    '2025-08-22T10:00:41-05:00 [DEBUG] Et consectetur velit laborum occaecat dolore sed mollit voluptate ipsum sint officia ut cupidatat cillum sunt ut cupidatat.',
    '2025-08-22T10:00:42-05:00 [INFO] Id commodo laborum qui in cupidatat commodo reprehenderit aliquip tempor.',
    '2025-08-22T10:00:43-05:00 [WARN] Proident aliquip in eu voluptate sit deserunt reprehenderit veniam officia ullamco esse.',
    '2025-08-22T10:00:44-05:00 [ERROR] Voluptate consequat consequat ipsum id quis eiusmod ut excepteur officia ut culpa.',
    '2025-08-22T10:00:45-05:00 [TRACE] Officia proident dolor tempor aute laboris pariatur aliquip dolor dolore culpa est velit occaecat in esse sunt commodo.',
    '2025-08-22T10:00:46-05:00 [DEBUG] Ex nisi et quis in et laborum veniam quis ullamco qui consequat.',
    '2025-08-22T10:00:47-05:00 [INFO] Est duis incididunt quis aute nisi cillum minim irure ipsum laborum dolore consequat consectetur adipiscing aute dolore.',
    '2025-08-22T10:00:48-05:00 [WARN] Officia ut ipsum duis culpa qui non voluptate veniam adipiscing ex qui labore sed pariatur officia do adipiscing.',
    '2025-08-22T10:00:49-05:00 [ERROR] Ut irure eiusmod aliquip et sint laboris id eu proident.',
    '2025-08-22T10:00:50-05:00 [TRACE] Irure occaecat dolor elit incididunt exercitation ullamco ea eiusmod enim ut minim do enim lorem.',
    '2025-08-22T10:00:51-05:00 [DEBUG] Proident culpa aute amet nisi duis duis sunt do nisi ea nostrud occaecat labore.',
    '2025-08-22T10:00:52-05:00 [INFO] Laboris ut commodo aliqua do elit ad dolor duis non et in irure pariatur commodo mollit.',
    '2025-08-22T10:00:53-05:00 [WARN] Deserunt non eiusmod consectetur cupidatat reprehenderit ex sit tempor nisi dolor commodo consectetur minim culpa id.',
    '2025-08-22T10:00:54-05:00 [ERROR] Non consequat veniam cupidatat officia tempor culpa velit excepteur in reprehenderit ut enim in excepteur deserunt duis pariatur.',
    '2025-08-22T10:00:55-05:00 [TRACE] Amet sunt tempor in ex reprehenderit labore pariatur anim lorem in excepteur adipiscing quis id cillum.',
    '2025-08-22T10:00:56-05:00 [DEBUG] Deserunt non adipiscing exercitation commodo dolore duis non officia et sit ut enim dolor ipsum excepteur tempor.',
    '2025-08-22T10:00:57-05:00 [INFO] Labore in et ut deserunt aute anim commodo sint qui culpa.',
    '2025-08-22T10:00:58-05:00 [WARN] Sunt aliqua fugiat quis anim magna sed consequat sint voluptate mollit.',
    '2025-08-22T10:00:59-05:00 [ERROR] Lorem duis irure officia ut proident laborum qui velit in eu sunt.',
    '2025-08-22T10:01:00-05:00 [TRACE] Quis ut fugiat nisi excepteur consectetur in culpa eu fugiat ut deserunt amet.',
  ];

  const minPriority = LOG_PRIORITY[minLevel];

  return allLogs.filter((line) => {
    const levelMatch = LOG_LEVELS.find((lvl) => line.includes(lvl));
    if (!levelMatch) return false;

    const logPriority = LOG_PRIORITY[levelMatch];
    const passesLevel = logPriority >= minPriority;
    const passesText = contains === '' || line.toLowerCase().includes(contains.toLowerCase());

    return passesLevel && passesText;
  });
};

export default function LogViewer() {
  const [logLevel, setLogLevel] = useState<LogLevel>('INFO');
  const [contains, setContains] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [matches, setMatches] = useState<number[]>([]);
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    async function fetchLogs() {
      const result = await mockFetchLogs(logLevel, contains);
      setLogs(result);
    }
    fetchLogs();
  }, [logLevel, contains]);

  useEffect(() => {
    const found: number[] = [];
    logs.forEach((line, index) => {
      if (searchTerm && line.toLowerCase().includes(searchTerm.toLowerCase())) {
        found.push(index);
      }
    });
    setMatches(found);
    setCurrentMatchIndex(0);
  }, [searchTerm, logs]);

  const goToNext = () => {
    setCurrentMatchIndex((prev) => (prev + 1) % matches.length);
    scrollToMatch((currentMatchIndex + 1) % matches.length);
  };

  const goToPrev = () => {
    setCurrentMatchIndex((prev) => (prev - 1 + matches.length) % matches.length);
    scrollToMatch((currentMatchIndex - 1 + matches.length) % matches.length);
  };

  const scrollToMatch = (index: number) => {
    const line = matches[index];
    const lines = textareaRef.current?.value.split('\n') || [];
    const charIndex = lines.slice(0, line).join('\n').length + line;
    textareaRef.current?.setSelectionRange(charIndex, charIndex + lines[line].length);
    textareaRef.current?.focus();
  };

  const renderedLogs = logs.map((line, index) => {
    const isMatch = matches.includes(index);
    return isMatch ? `>> ${line}` : line;
  });

  return (
    <SpaceBetween size="s">
      <Header>Viewing logs of Lorem Ipsum</Header>
      <KeyValuePairs items={[{
        label: "Log Path",
        value: "/shared-logs-output/imaginary/lorem-ipsum.log"
      }]}></KeyValuePairs>
      <SpaceBetween direction="horizontal" size="xl">
        <FormField label="Log Level Filter" description="Filter the log data to only the level specified or higher.">
          <Select
            selectedOption={{ label: logLevel, value: logLevel }}
            onChange={({ detail }) =>
              setLogLevel((detail.selectedOption.value as LogLevel) || 'INFO')
            }
            options={LOG_LEVELS.map((lvl) => ({ label: lvl, value: lvl }))}
            selectedAriaLabel="Log Level"
          />
        </FormField>
      <FormField label="Highlight term" description="Highlights a term in the log output">
        <Input
          placeholder="Client search..."
          value={searchTerm}
          onChange={({ detail }) => setSearchTerm(detail.value)}
        />
        </FormField>
        <FormField label="Hightlight matches" description="The number of matches for the hightlighted term">
        <Box variant="span">
          {matches.length > 0 ? `${currentMatchIndex + 1} of ${matches.length}` : 'No matches'}
        </Box>
        </FormField>
      </SpaceBetween>

<div
  style={{
    maxHeight: '400px',
    overflowY: 'auto',
    fontFamily: 'monospace',
    whiteSpace: 'pre-wrap',
    backgroundColor: '#f9f9f9',
    border: '1px solid #ccc',
    padding: '1rem',
    borderRadius: '4px',
  }}
>
  {logs.map((line, idx) => {
    const isMatch = searchTerm && line.toLowerCase().includes(searchTerm.toLowerCase());

    const level = LOG_LEVELS.find((lvl) => line.startsWith(lvl)) || 'INFO';

    const styledLine = isMatch
      ? line.replace(
          new RegExp(searchTerm, 'gi'),
          (match) => `<span class="highlight">${match}</span>`
        )
      : line;

    return (
      <div
        key={idx}
        className={`log-line log-${level.toLowerCase()}`}
        dangerouslySetInnerHTML={{ __html: styledLine }}
      />
    );
  })}
</div>

    </SpaceBetween>
  );
}