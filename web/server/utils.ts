export const green = (strings: TemplateStringsArray, ...values: any[]) => {
  const greenColorCode = "\x1b[32m"; // ANSI escape code for green
  const resetCode = "\x1b[0m"; // ANSI escape code to reset color

  return strings
    .reduce((result, string, i) => {
      const value = values[i] !== undefined ? values[i] : "";
      return result + string + value;
    }, "")
    .replace(/(.*)/g, `${greenColorCode}$1${resetCode}`);
};
