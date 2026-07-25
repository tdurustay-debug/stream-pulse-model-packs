import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "..");
const schemaPath = path.join(
  repositoryRoot,
  "schemas",
  "model-manifest.schema.json",
);
const manifestPath = path.join(
  repositoryRoot,
  "manifest",
  "v1",
  "model-manifest.json",
);

const expectedContextPacks = new Map([
  ["context-qwen3-0.6b", "low-system"],
  ["context-qwen3-1.7b", "high-accuracy"],
]);

const expectedLanguagePromptPacks = new Map([
  ["prompt-en-US", "en-US"],
  ["prompt-es-ES", "es-ES"],
  ["prompt-pt-BR", "pt-BR"],
  ["prompt-ru-RU", "ru-RU"],
  ["prompt-de-DE", "de-DE"],
  ["prompt-fr-FR", "fr-FR"],
  ["prompt-ja-JP", "ja-JP"],
  ["prompt-it-IT", "it-IT"],
  ["prompt-pl-PL", "pl-PL"],
  ["prompt-tr-TR", "tr-TR"],
]);

const expectedProfileContents = new Set([
  "analysis_instructions",
  "twitch_terminology",
  "common_slang_examples",
  "sarcasm_examples",
  "playful_insult_examples",
  "technical_complaint_examples",
  "output_labels",
  "confidence_thresholds",
]);

const failures = [];

function addFailure(message) {
  failures.push(message);
}

function findDuplicates(values) {
  const seen = new Set();
  const duplicates = new Set();

  for (const value of values) {
    if (seen.has(value)) {
      duplicates.add(value);
    }
    seen.add(value);
  }

  return [...duplicates];
}

function requireReadyValue(pack, field) {
  const value = pack[field];
  if (
    value === null ||
    value === undefined ||
    (typeof value === "string" && value.trim() === "")
  ) {
    addFailure(`Ready pack "${pack.id}" is missing ${field}.`);
  }
}

try {
  const [schemaText, manifestText] = await Promise.all([
    readFile(schemaPath, "utf8"),
    readFile(manifestPath, "utf8"),
  ]);
  const schema = JSON.parse(schemaText);
  const manifest = JSON.parse(manifestText);

  const ajv = new Ajv2020({
    allErrors: true,
    strict: true,
  });
  addFormats(ajv);
  const validate = ajv.compile(schema);

  if (!validate(manifest)) {
    for (const error of validate.errors ?? []) {
      addFailure(
        `Schema error at ${error.instancePath || "/"}: ${error.message}`,
      );
    }
  }

  const packs = [
    ...manifest.contextAnalysisPacks,
    ...manifest.languagePromptPacks,
    ...manifest.ruleInterpreterPacks,
    ...manifest.speechRecognitionPacks,
  ];

  for (const duplicateId of findDuplicates(packs.map((pack) => pack.id))) {
    addFailure(`Duplicate pack ID: ${duplicateId}`);
  }

  const readyPacks = packs.filter((pack) => pack.status === "ready");
  for (const duplicateUrl of findDuplicates(
    readyPacks.map((pack) => pack.downloadUrl),
  )) {
    addFailure(`Duplicate ready download URL: ${duplicateUrl}`);
  }
  for (const duplicateFileName of findDuplicates(
    readyPacks.map((pack) => pack.fileName),
  )) {
    addFailure(`Duplicate ready filename: ${duplicateFileName}`);
  }

  const requiredReadyModelValues = [
    "version",
    "runtime",
    "format",
    "sourceModel",
    "sourceRevision",
    "sourceUrl",
    "licenseId",
    "licenseFile",
    "attributionFile",
    "fileName",
    "downloadUrl",
    "sizeBytes",
    "minimumRamMb",
    "recommendedRamMb",
    "minimumCpuThreads",
    "evaluationNotes",
  ];

  const readyModelPacks = readyPacks.filter(
    (pack) => pack.type !== "language-prompt",
  );
  for (const pack of readyModelPacks) {
    for (const field of requiredReadyModelValues) {
      requireReadyValue(pack, field);
    }
    if (pack.redistributable !== true) {
      addFailure(`Ready pack "${pack.id}" is not approved for redistribution.`);
    }
    if (pack.commercialUseAllowed !== true) {
      addFailure(`Ready pack "${pack.id}" is not approved for commercial use.`);
    }
    if (typeof pack.modificationAllowed !== "boolean") {
      addFailure(
        `Ready pack "${pack.id}" has no modification-rights determination.`,
      );
    }
    if (!/^[a-fA-F0-9]{64}$/.test(pack.sha256 ?? "")) {
      addFailure(`Ready pack "${pack.id}" has no valid SHA-256 value.`);
    }
    if (!Array.isArray(pack.backupLocations) || pack.backupLocations.length < 2) {
      addFailure(
        `Ready pack "${pack.id}" must have at least two backup locations.`,
      );
    }
    if (pack.evaluationStatus !== "passed") {
      addFailure(`Ready pack "${pack.id}" has not passed evaluation.`);
    }
  }

  const readyPromptPacks = readyPacks.filter(
    (pack) => pack.type === "language-prompt",
  );
  for (const pack of readyPromptPacks) {
    for (const field of [
      "version",
      "format",
      "fileName",
      "downloadUrl",
      "sizeBytes",
      "evaluationNotes",
    ]) {
      requireReadyValue(pack, field);
    }
    if (pack.containsModelWeights !== false) {
      addFailure(`Language prompt pack "${pack.id}" must not contain weights.`);
    }
    if (!/^[a-fA-F0-9]{64}$/.test(pack.sha256 ?? "")) {
      addFailure(`Ready pack "${pack.id}" has no valid SHA-256 value.`);
    }
    if (!Array.isArray(pack.backupLocations) || pack.backupLocations.length < 2) {
      addFailure(
        `Ready pack "${pack.id}" must have at least two backup locations.`,
      );
    }
    if (pack.evaluationStatus !== "passed") {
      addFailure(`Ready pack "${pack.id}" has not passed evaluation.`);
    }
  }

  for (const [id, mode] of expectedContextPacks) {
    const matchingPacks = manifest.contextAnalysisPacks.filter(
      (pack) =>
        pack.id === id &&
        pack.type === "context-analysis" &&
        pack.mode === mode &&
        pack.language === "multilingual",
    );
    if (matchingPacks.length !== 1) {
      addFailure(
        `Expected exactly one context-analysis pack "${id}" for mode "${mode}".`,
      );
    }
  }

  if (manifest.contextAnalysisPacks.length !== expectedContextPacks.size) {
    addFailure(
      `Expected exactly ${expectedContextPacks.size} context-analysis packs, found ${manifest.contextAnalysisPacks.length}.`,
    );
  }

  for (const [id, language] of expectedLanguagePromptPacks) {
    const matchingPacks = manifest.languagePromptPacks.filter(
      (pack) =>
        pack.id === id &&
        pack.type === "language-prompt" &&
        pack.language === language &&
        pack.containsModelWeights === false,
    );
    if (matchingPacks.length !== 1) {
      addFailure(
        `Expected exactly one weight-free language prompt pack "${id}" for ${language}.`,
      );
      continue;
    }

    const actualContents = new Set(matchingPacks[0].profileContents);
    if (
      actualContents.size !== expectedProfileContents.size ||
      [...expectedProfileContents].some((item) => !actualContents.has(item))
    ) {
      addFailure(
        `Language prompt pack "${id}" does not declare every required profile section.`,
      );
    }
  }

  if (manifest.languagePromptPacks.length !== expectedLanguagePromptPacks.size) {
    addFailure(
      `Expected exactly ${expectedLanguagePromptPacks.size} language prompt packs, found ${manifest.languagePromptPacks.length}.`,
    );
  }

  if (failures.length > 0) {
    console.error(`Manifest validation failed with ${failures.length} error(s):`);
    for (const failure of failures) {
      console.error(`- ${failure}`);
    }
    process.exitCode = 1;
  } else {
    console.log(
      `Manifest validation succeeded: ${packs.length} planned pack entries are schema-valid and repository checks passed.`,
    );
  }
} catch (error) {
  console.error(`Manifest validation could not run: ${error.message}`);
  process.exitCode = 1;
}
