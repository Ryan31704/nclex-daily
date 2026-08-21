import { useState } from 'react'

import type { PracticeQuestion, SubmitAnswerResponse } from '../types/practice'
import { AnswerChoiceButton } from './AnswerChoiceButton'

interface Props {
  question: PracticeQuestion
  feedback: SubmitAnswerResponse | null
  disabled: boolean
  onSubmit: (answer: unknown) => void
}

interface TextChoice { id: string; text: string }
interface LabeledGroup { choices: TextChoice[]; required_count?: number }

const buttonClass = 'min-h-11 rounded-xl border-2 border-slate-200 bg-white px-4 py-2 text-left font-semibold text-ink transition hover:border-teal-400 disabled:opacity-60'
const selectedClass = 'border-teal-600 bg-teal-50 ring-2 ring-teal-100'

function ChoiceQuestions({ question, feedback, disabled, onSubmit }: Props) {
  const multiple = question.question_type === 'multiple_response'
  const ordered = question.question_type === 'ordered_response'
  const [selected, setSelected] = useState<string[]>([])
  const expected = Array.isArray(feedback?.correct_response)
    ? feedback.correct_response.map(String)
    : feedback?.correct_response ? [String(feedback.correct_response)] : []

  if (!multiple && !ordered) {
    return <>{question.choices.map((choice, index) => {
      let state: 'idle' | 'correct' | 'incorrect' | 'muted' = 'idle'
      if (feedback) {
        if (expected.includes(choice.id)) state = 'correct'
        else if (selected.includes(choice.id)) state = 'incorrect'
        else state = 'muted'
      }
      return <AnswerChoiceButton disabled={disabled} key={choice.id} letter={String.fromCharCode(65 + index)} onSelect={() => { setSelected([choice.id]); onSubmit(choice.id) }} state={state} text={choice.choice_text} />
    })}</>
  }

  const toggle = (id: string) => {
    if (disabled) return
    setSelected((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id])
  }
  return <div className="space-y-3">
    {question.choices.map((choice, index) => {
      const chosenIndex = selected.indexOf(choice.id)
      const correct = feedback && expected.includes(choice.id)
      const wrong = feedback && chosenIndex >= 0 && !correct
      return <button className={`${buttonClass} flex w-full items-center gap-3 ${chosenIndex >= 0 ? selectedClass : ''} ${correct ? '!border-emerald-500 !bg-emerald-50' : ''} ${wrong ? '!border-rose-400 !bg-rose-50' : ''}`} disabled={disabled} key={choice.id} onClick={() => toggle(choice.id)} type="button">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-current/15 bg-white text-sm font-extrabold">{ordered && chosenIndex >= 0 ? chosenIndex + 1 : String.fromCharCode(65 + index)}</span>
        <span>{choice.choice_text}</span>
      </button>
    })}
    {!feedback ? <button className="mt-3 min-h-12 w-full rounded-2xl bg-teal-600 px-6 font-extrabold text-white disabled:opacity-50" disabled={disabled || selected.length === 0} onClick={() => onSubmit(selected)} type="button">SUBMIT ANSWER</button> : null}
    <p className="text-center text-sm font-semibold text-slate-500">{ordered ? 'Tap choices in the correct order.' : 'Select every answer that applies.'}</p>
  </div>
}

function StructuredQuestion({ question, feedback, disabled, onSubmit }: Props) {
  const interaction = question.interaction ?? {}
  const [value, setValue] = useState<Record<string, string | string[]>>({})
  const setOne = (key: string, item: string) => setValue((current) => ({ ...current, [key]: item }))
  const toggle = (key: string, item: string, limit?: number) => setValue((current) => {
    const list = Array.isArray(current[key]) ? current[key] as string[] : []
    const next = list.includes(item) ? list.filter((entry) => entry !== item) : [...list, item]
    return { ...current, [key]: limit ? next.slice(-limit) : next }
  })

  let content
  if (question.question_type === 'numeric_response') {
    content = <label className="block text-sm font-bold text-slate-700">Your numeric answer<input className="mt-2 min-h-12 w-full rounded-xl border-2 border-slate-200 px-4 text-lg focus:border-teal-500 focus:outline-none" disabled={disabled} inputMode="decimal" onChange={(event) => setOne('value', event.target.value)} type="number" /></label>
  } else if (question.question_type === 'highlight') {
    const tokens = (interaction.tokens ?? []) as TextChoice[]
    content = <div className="space-y-2">{tokens.map((token) => <button className={`${buttonClass} w-full ${Array.isArray(value.correct_token_ids) && value.correct_token_ids.includes(token.id) ? selectedClass : ''}`} disabled={disabled} key={token.id} onClick={() => toggle('correct_token_ids', token.id)} type="button">{token.text}</button>)}</div>
  } else if (question.question_type === 'cloze') {
    const blanks = (interaction.blanks ?? []) as Array<{ id: string; label: string; choices: TextChoice[] }>
    content = <div className="space-y-4">{blanks.map((blank) => <label className="block text-sm font-bold text-slate-700" key={blank.id}>{blank.label}<select className="mt-2 min-h-12 w-full rounded-xl border-2 border-slate-200 bg-white px-3" disabled={disabled} onChange={(event) => setOne(blank.id, event.target.value)} value={typeof value[blank.id] === 'string' ? value[blank.id] : ''}><option value="">Choose…</option>{blank.choices.map((choice) => <option key={choice.id} value={choice.id}>{choice.text}</option>)}</select></label>)}</div>
  } else if (question.question_type === 'matching') {
    const rows = (interaction.rows ?? []) as TextChoice[]; const targets = (interaction.targets ?? []) as TextChoice[]
    content = <div className="space-y-4">{rows.map((row) => <label className="block text-sm font-bold text-slate-700" key={row.id}>{row.text}<select className="mt-2 min-h-12 w-full rounded-xl border-2 border-slate-200 bg-white px-3" disabled={disabled} onChange={(event) => setOne(row.id, event.target.value)} value={typeof value[row.id] === 'string' ? value[row.id] : ''}><option value="">Match to…</option>{targets.map((target) => <option key={target.id} value={target.id}>{target.text}</option>)}</select></label>)}</div>
  } else if (question.question_type === 'matrix') {
    const rows = (interaction.rows ?? []) as TextChoice[]; const columns = (interaction.columns ?? []) as TextChoice[]
    content = <div className="overflow-x-auto"><table className="w-full min-w-[32rem] border-separate border-spacing-2"><thead><tr><th /><>{columns.map((column) => <th className="p-2 text-sm" key={column.id}>{column.text}</th>)}</></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><th className="p-2 text-left text-sm">{row.text}</th>{columns.map((column) => <td className="text-center" key={column.id}><input checked={Array.isArray(value[row.id]) && value[row.id].includes(column.id)} className="h-5 w-5 accent-teal-600" disabled={disabled} onChange={() => toggle(row.id, column.id)} type="checkbox" /></td>)}</tr>)}</tbody></table></div>
  } else {
    const condition = interaction.condition as LabeledGroup; const actions = interaction.actions as LabeledGroup; const parameters = interaction.parameters as LabeledGroup
    content = <div className="space-y-5"><ChoiceGroup disabled={disabled} group={condition} label="Condition" mode="one" selected={value.condition_choice_id} setOne={(id) => setOne('condition_choice_id', id)} toggle={() => undefined} /><ChoiceGroup disabled={disabled} group={actions} label={`Actions — choose ${actions.required_count ?? 2}`} mode="many" selected={value.action_choice_ids} setOne={() => undefined} toggle={(id) => toggle('action_choice_ids', id, actions.required_count)} /><ChoiceGroup disabled={disabled} group={parameters} label={`Parameters — choose ${parameters.required_count ?? 2}`} mode="many" selected={value.parameter_choice_ids} setOne={() => undefined} toggle={(id) => toggle('parameter_choice_ids', id, parameters.required_count)} /></div>
  }
  const answer = question.question_type === 'numeric_response' ? value.value : question.question_type === 'cloze' ? { blank_to_correct_choice_id: value } : question.question_type === 'matching' ? { row_to_correct_target_id: value } : question.question_type === 'matrix' ? { row_to_correct_column_ids: value } : value
  return <div>{content}{!feedback ? <button className="mt-5 min-h-12 w-full rounded-2xl bg-teal-600 px-6 font-extrabold text-white disabled:opacity-50" disabled={disabled || Object.keys(value).length === 0} onClick={() => onSubmit(answer)} type="button">SUBMIT ANSWER</button> : null}</div>
}

function ChoiceGroup({ group, label, mode, selected, setOne, toggle, disabled }: { group: LabeledGroup; label: string; mode: 'one' | 'many'; selected: string | string[] | undefined; setOne: (id: string) => void; toggle: (id: string) => void; disabled: boolean }) {
  const values = Array.isArray(selected) ? selected : selected ? [selected] : []
  return <fieldset><legend className="mb-2 font-extrabold text-ink">{label}</legend><div className="grid gap-2 sm:grid-cols-2">{group.choices.map((choice) => <button className={`${buttonClass} ${values.includes(choice.id) ? selectedClass : ''}`} disabled={disabled} key={choice.id} onClick={() => mode === 'one' ? setOne(choice.id) : toggle(choice.id)} type="button">{choice.text}</button>)}</div></fieldset>
}

export function QuestionInteraction(props: Props) {
  if (['multiple_choice', 'multiple_response', 'ordered_response'].includes(props.question.question_type)) return <ChoiceQuestions {...props} />
  return <StructuredQuestion {...props} />
}
