
How to create the year month format
You can use the below steps to translate the code to a Python code.
These are just some helpful suggestions on how to display the date by create a separate model.
Create a model for the date.
And try to translate the below React code into corresponding Python code.

function ExpenseDate(props) {
  const month = props.date.toLocaleString("en-US", { month: "long" });
  const year = props.date.getFullYear();

  return (
    <div className="expense-date">
      <div>
        {month} {year}
      </div>
  
  );
}

export default ExpenseDate;
